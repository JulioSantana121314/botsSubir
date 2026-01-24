import sys
from pathlib import Path
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import local, Semaphore
from functools import lru_cache
from time import time
import os

from config import companies, SUPERADMIN_USER, SUPERADMIN_PASS, insertar_movimientos, MONGODB_URI, MONGO_DATABASE

sys.path.insert(0, str(Path(__file__).parent.parent))
from diccionario import GRUPOS_COMPANIAS

from pipeline_balances import ejecutar_pipeline_grupo, exportar_a_sheets, enviar_a_backend

# ===== CONFIGURACIÓN DE RENDIMIENTO =====
MAX_WORKERS_COMPANIAS = min(20, (os.cpu_count() or 1) * 4)
MAX_WORKERS_FECHAS = 5
MAX_WORKERS_GRUPOS = 3
PAGE_SIZE = 2000
TOKEN_TTL = 3600
MAX_CONCURRENT_REQUESTS = 50  # Rate limiting

_thread_local = local()
_token_cache = {}
_rate_limiter = Semaphore(MAX_CONCURRENT_REQUESTS)


def get_session():
    """Session con connection pooling y retry automático"""
    if not hasattr(_thread_local, "session"):
        session = requests.Session()
        adapter = HTTPAdapter(
            pool_connections=10,
            pool_maxsize=20,
            max_retries=Retry(
                total=3, 
                backoff_factor=0.3, 
                status_forcelist=[500, 502, 503, 504, 429]  # Incluye 429 (rate limit)
            )
        )
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        _thread_local.session = session
    return _thread_local.session


def cleanup_sessions():
    """Cierra todas las sesiones abiertas"""
    if hasattr(_thread_local, "session"):
        try:
            _thread_local.session.close()
        except:
            pass


def obtener_token_compania(nombre_compania):
    """Obtiene token con cache de 1 hora"""
    session = get_session()

    # Cache check
    now = time()
    if nombre_compania in _token_cache:
        token, company_id, timestamp = _token_cache[nombre_compania]
        if now - timestamp < TOKEN_TTL:
            return token, company_id

    login_url = "https://api.backend.biz/api/authentication/login/backend"
    login_data = {"username": SUPERADMIN_USER, "password": SUPERADMIN_PASS}

    with _rate_limiter:
        resp = session.post(login_url, json=login_data, timeout=30)
        resp.raise_for_status()
        super_token = resp.json()["data"]["token"]

    company_id = companies[nombre_compania]
    change_url = "https://api.backend.biz/api/authentication/change-company/master"
    headers = {"Authorization": f"Bearer {super_token}"}
    payload = {"companyId": company_id}

    with _rate_limiter:
        cambio = session.post(change_url, json=payload, headers=headers, timeout=30)
        cambio.raise_for_status()
        data = cambio.json()

    token = data.get("token") or data.get("data", {}).get("token")

    if not token:
        raise ValueError(f"No se pudo obtener token para {nombre_compania}")

    # Cache token
    _token_cache[nombre_compania] = (token, company_id, now)
    return token, company_id


def extraer_movimientos(nombre_compania, token, company_id, fecha, timestamp_extraccion):
    """Extrae movimientos de una fecha específica con rate limiting"""
    session = get_session()
    headers = {"Authorization": f"Bearer {token}"}
    movements_url = "https://api.backend.biz/api/movements/paginated"

    date_filter = f"{fecha},{fecha}"
    params = {
        "filters": f'''[{{"type":"date","value":"{date_filter}"}},{{"type":"companyId","value":"{company_id}"}}]''',
        "page": 1,
        "pageSize": PAGE_SIZE,
        "timeZone": "America/Lima",
    }

    with _rate_limiter:
        resp = session.get(movements_url, params=params, headers=headers, timeout=45)
        resp.raise_for_status()
        json_data = resp.json()

    total_docs = json_data.get("data", {}).get("numberTotalDocuments", 0)
    total_pages = (total_docs // PAGE_SIZE) + (1 if total_docs % PAGE_SIZE else 0)

    all_documents = []
    for page in range(1, total_pages + 1):
        params["page"] = page

        with _rate_limiter:
            resp = session.get(movements_url, params=params, headers=headers, timeout=45)
            resp.raise_for_status()
            documents = resp.json().get("data", {}).get("documents", [])
            all_documents.extend(documents)

    for doc in all_documents:
        doc["timestamp_extraccion"] = timestamp_extraccion

    return all_documents


def procesar_compania_multi_fecha(nombre_compania, fechas, timestamp_extraccion):
    """Procesa una compañía descargando fechas en paralelo"""
    tiempo_inicio = time()

    try:
        token, company_id = obtener_token_compania(nombre_compania)

        todos_movimientos = []
        fechas_fallidas = []

        # Paralelizar descarga de fechas
        with ThreadPoolExecutor(max_workers=MAX_WORKERS_FECHAS) as fecha_exec:
            future_fechas = {
                fecha_exec.submit(extraer_movimientos, nombre_compania, token, company_id, fecha, timestamp_extraccion): fecha
                for fecha in fechas
            }

            for future in as_completed(future_fechas):
                fecha = future_fechas[future]
                try:
                    movs = future.result()
                    todos_movimientos.extend(movs)
                except Exception as e:
                    print(f"    ✗ Error en {fecha}: {e}")
                    fechas_fallidas.append(fecha)

        # Insertar solo si hay movimientos
        if todos_movimientos:
            insertar_movimientos(todos_movimientos, nombre_compania)

        duracion = time() - tiempo_inicio

        # Determinar status
        if fechas_fallidas:
            if len(fechas_fallidas) == len(fechas):
                status = "error"
            else:
                status = "partial"
        else:
            status = "success"

        return {
            "compania": nombre_compania, 
            "status": status,
            "count": len(todos_movimientos),
            "fechas": fechas,
            "fechas_fallidas": fechas_fallidas,
            "duracion": duracion
        }
    except Exception as e:
        print(f"  ✗ [{nombre_compania}] Error: {e}")
        return {
            "compania": nombre_compania, 
            "status": "error", 
            "error": str(e),
            "fechas": fechas,
            "duracion": time() - tiempo_inicio
        }


def analizar_fechas_necesarias_por_grupo():
    """Analiza balances y detecta qué fechas descargar (paralelo por grupo)"""
    from pymongo import MongoClient
    from collections import defaultdict
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    fechas_por_compania = defaultdict(set)
    
    print("\n" + "="*80)
    print("📅 ANALIZANDO FECHAS NECESARIAS")
    print("="*80)
    
    def procesar_grupo_fechas(grupo):
        """Procesa un grupo y retorna fechas por compañía"""
        client = MongoClient(
            MONGODB_URI, 
            maxPoolSize=10,
            serverSelectionTimeoutMS=5000,
            socketTimeoutMS=30000
        )
        db = client[MONGO_DATABASE]
        col_balances = db["balances_bot"]
        
        pipeline = [
            {"$match": {
                "used_as_previous": False,
                "grupo": grupo
            }},
            {"$sort": {"website": 1, "username": 1, "fecha": -1}},
            {"$group": {
                "_id": {"website": "$website", "username": "$username"},
                "fechas": {"$push": "$fecha"}
            }},
            {"$project": {
                "fecha_actual": {"$arrayElemAt": ["$fechas", 0]},
                "fecha_anterior": {"$arrayElemAt": ["$fechas", 1]}
            }},
            {"$match": {"fecha_anterior": {"$ne": None}}}
        ]
        
        resultados = list(col_balances.aggregate(pipeline, allowDiskUse=True))
        client.close()
        
        fechas_grupo = defaultdict(set)
        
        for doc in resultados:
            fecha_actual = datetime.strptime(doc["fecha_actual"], "%Y-%m-%d %H:%M:%S")
            fecha_anterior = datetime.strptime(doc["fecha_anterior"], "%Y-%m-%d %H:%M:%S")
            
            fecha_inicio = fecha_anterior.date()
            fecha_fin = fecha_actual.date()
            
            current = fecha_inicio
            while current <= fecha_fin:
                fecha_str = current.strftime("%Y-%m-%d")
                
                for compania in GRUPOS_COMPANIAS.get(grupo, []):
                    if compania in companies:
                        fechas_grupo[compania].add(fecha_str)
                
                current += timedelta(days=1)
        
        return fechas_grupo
    
    # Procesar grupos en paralelo
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            executor.submit(procesar_grupo_fechas, grupo): grupo 
            for grupo in GRUPOS_COMPANIAS.keys()
        }
        
        for future in as_completed(futures):
            fechas_grupo = future.result()
            for compania, fechas in fechas_grupo.items():
                fechas_por_compania[compania].update(fechas)
    
    resultado = {
        compania: sorted(list(fechas))
        for compania, fechas in fechas_por_compania.items()
    }
    
    total_fechas = len(set(f for fechas in resultado.values() for f in fechas))
    print(f"  ✓ {len(resultado)} compañías | {total_fechas} fechas únicas")
    print("="*80 + "\n")
    
    return resultado


def procesar_grupo(grupo, companias_con_fechas):
    """Procesa un grupo completo"""
    print(f"\n{'='*80}")
    print(f"GRUPO: {grupo} ({len(companias_con_fechas)} compañías)")
    print(f"{'='*80}\n")

    timestamp_grupo = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    resultados = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS_COMPANIAS) as executor:
        futures = {
            executor.submit(procesar_compania_multi_fecha, compania, fechas, timestamp_grupo): compania 
            for compania, fechas in companias_con_fechas
        }

        for future in as_completed(futures):
            resultado = future.result()
            resultados.append(resultado)

            if resultado["status"] == "success":
                print(f"  ✓ [{resultado['compania']}] {resultado['count']} movs | {len(resultado['fechas'])} fechas | {resultado['duracion']:.1f}s")
            elif resultado["status"] == "partial":
                print(f"  ⚠ [{resultado['compania']}] {resultado['count']} movs | {len(resultado['fechas_fallidas'])}/{len(resultado['fechas'])} fechas fallidas")
            else:
                print(f"  ✗ [{resultado['compania']}] Error total")

    exitosos = sum(1 for r in resultados if r["status"] in ["success", "partial"])
    fallidos = sum(1 for r in resultados if r["status"] == "error")

    print(f"\n📊 {grupo}: ✓ {exitosos} | ✗ {fallidos}")

    # Pipeline
    resultados_pipeline = ejecutar_pipeline_grupo(grupo, timestamp_grupo)
    print(f"  ✓ Pipeline: {len(resultados_pipeline)} balances\n")

    return resultados_pipeline


if __name__ == "__main__":
    from collections import defaultdict

    tiempo_inicio = datetime.now()

    try:
        print("\n" + "="*80)
        print("EXTRACCIÓN OPTIMIZADA DE MOVIMIENTOS")
        print(f"Workers: Compañías={MAX_WORKERS_COMPANIAS} | Fechas={MAX_WORKERS_FECHAS} | Grupos={MAX_WORKERS_GRUPOS}")
        print(f"Rate Limit: {MAX_CONCURRENT_REQUESTS} requests concurrentes")
        print("="*80)

        fechas_por_compania = analizar_fechas_necesarias_por_grupo()

        if not fechas_por_compania:
            print("\n⚠️  No hay balances pendientes\n")
            exit(0)

        # Agrupar compañías por grupo
        companias_por_grupo = defaultdict(list)
        for compania, fechas in fechas_por_compania.items():
            for grupo, companias_grupo in GRUPOS_COMPANIAS.items():
                if compania in companias_grupo:
                    companias_por_grupo[grupo].append((compania, fechas))
                    break

        todos_resultados = []

        # Procesar grupos en paralelo
        with ThreadPoolExecutor(max_workers=MAX_WORKERS_GRUPOS) as grupo_exec:
            future_grupos = {
                grupo_exec.submit(procesar_grupo, grupo, companias): grupo
                for grupo, companias in companias_por_grupo.items()
            }

            for future in as_completed(future_grupos):
                grupo = future_grupos[future]
                try:
                    resultados = future.result()
                    todos_resultados.extend(resultados)
                except Exception as e:
                    print(f"\n❌ Error procesando grupo {grupo}: {e}\n")

        # Exportar
        print("\n" + "="*80)
        print("EXPORTACIÓN FINAL")
        print("="*80 + "\n")
        exportar_a_sheets(todos_resultados)
        enviar_a_backend(todos_resultados, tiempo_inicio)

        duracion = (datetime.now() - tiempo_inicio).total_seconds()
        print(f"\n✅ COMPLETADO en {duracion:.1f}s\n")

    finally:
        # Cleanup de sesiones
        cleanup_sessions()
