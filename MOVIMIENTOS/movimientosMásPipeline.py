import sys
from pathlib import Path
import requests
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from config import companies, SUPERADMIN_USER, SUPERADMIN_PASS, insertar_movimientos, MONGODB_URI, MONGO_DATABASE

# Solo diccionario está en la carpeta anterior
sys.path.insert(0, str(Path(__file__).parent.parent))
from diccionario import GRUPOS_COMPANIAS

# Importar las nuevas funciones de pipeline
from pipeline_balances import ejecutar_pipeline_grupo, exportar_a_sheets, enviar_a_backend

def analizar_fechas_necesarias_por_grupo():
    from pymongo import MongoClient
    from collections import defaultdict
    from datetime import datetime, timedelta
    
    client = MongoClient(MONGODB_URI)
    db = client[MONGO_DATABASE]
    col_balances = db["balances_bot"]
    
    fechas_por_compania = defaultdict(set)
    
    print("\n" + "="*80)
    print("📅 ANALIZANDO FECHAS NECESARIAS POR GRUPO")
    print("="*80)
    
    for grupo, companias in GRUPOS_COMPANIAS.items():
        print(f"\n🔍 Grupo: {grupo}")
        
        # Pipeline para obtener pares de balances
        pipeline = [
            {"$match": {
                "grupo": grupo,
                "used_as_previous": False
            }},
            {"$sort": {"website": 1, "username": 1, "fecha": -1}},
            {"$group": {
                "_id": {"website": "$website", "username": "$username"},
                "balances": {"$push": {"fecha": "$fecha"}}
            }},
            {"$project": {
                "fecha_actual": {"$arrayElemAt": ["$balances.fecha", 0]},
                "fecha_anterior": {"$arrayElemAt": ["$balances.fecha", 1]}
            }},
            {"$match": {
                "fecha_anterior": {"$ne": None}
            }}
        ]
        
        resultados = list(col_balances.aggregate(pipeline))
        
        if not resultados:
            print(f"  ℹ️  No hay balances pendientes")
            continue
        
        fechas_grupo = set()
        
        for doc in resultados:
            fecha_actual = datetime.strptime(doc["fecha_actual"], "%Y-%m-%d %H:%M:%S")
            fecha_anterior = datetime.strptime(doc["fecha_anterior"], "%Y-%m-%d %H:%M:%S")
            
            # Obtener TODAS las fechas entre anterior y actual (inclusive)
            fecha_inicio = fecha_anterior.date()
            fecha_fin = fecha_actual.date()
            
            current = fecha_inicio
            while current <= fecha_fin:
                fecha_str = current.strftime("%Y-%m-%d")
                fechas_grupo.add(fecha_str)
                
                # Agregar a TODAS las compañías del grupo
                for compania in companias:
                    if compania in companies:
                        fechas_por_compania[compania].add(fecha_str)
                
                current += timedelta(days=1)
        
        if fechas_grupo:
            print(f"  ✓ Fechas necesarias: {sorted(fechas_grupo)}")
            print(f"  📦 Compañías afectadas: {len([c for c in companias if c in companies])}")
    
    client.close()
    
    # Convertir sets a listas ordenadas
    resultado = {
        compania: sorted(list(fechas))
        for compania, fechas in fechas_por_compania.items()
    }
    
    total_companias = len(resultado)
    total_fechas_unicas = len(set(f for fechas in resultado.values() for f in fechas))
    
    print(f"\n📊 RESUMEN:")
    print(f"  Total compañías: {total_companias}")
    print(f"  Fechas únicas a descargar: {sorted(set(f for fechas in resultado.values() for f in fechas))}")
    print("="*80 + "\n")
    
    return resultado


def obtener_token_compania(nombre_compania):
    login_url = "https://api.backend.biz/api/authentication/login/backend"
    login_data = {"username": SUPERADMIN_USER, "password": SUPERADMIN_PASS}
    resp = requests.post(login_url, json=login_data)
    super_token = resp.json()["data"]["token"]

    company_id = companies[nombre_compania]
    change_url = "https://api.backend.biz/api/authentication/change-company/master"
    headers = {"Authorization": f"Bearer {super_token}"}
    payload = {"companyId": company_id}
    cambio = requests.post(change_url, json=payload, headers=headers)
    data = cambio.json()
    token = data.get("token") or data.get("data", {}).get("token")
    if not token:
        raise ValueError(f"No se pudo obtener token para {nombre_compania}: {data}")
    return token, company_id

def extraer_movimientos(nombre_compania, token, company_id, fecha, timestamp_extraccion):
    headers = {"Authorization": f"Bearer {token}"}
    movements_url = "https://api.backend.biz/api/movements/paginated"
    page_size = 1000

    date_filter = f"{fecha},{fecha}"

    params = {
        "filters": f'''[{{"type":"date","value":"{date_filter}"}},{{"type":"companyId","value":"{company_id}"}}]''',
        "page": 1,
        "pageSize": page_size,
        "timeZone": "America/Lima",
    }

    resp = requests.get(movements_url, params=params, headers=headers)
    json_data = resp.json()
    total_docs = json_data.get("data", {}).get("numberTotalDocuments", 0)
    total_pages = (total_docs // page_size) + (1 if total_docs % page_size else 0)
    print(f"  → [{nombre_compania}] Total: {total_docs} movimientos en {total_pages} páginas")

    all_documents = []
    for page in range(1, total_pages + 1):
        params["page"] = page
        resp = requests.get(movements_url, params=params, headers=headers)
        documents = resp.json().get("data", {}).get("documents", [])
        all_documents.extend(documents)

    # Agregar timestamp de extracción a cada movimiento
    for doc in all_documents:
        doc["timestamp_extraccion"] = timestamp_extraccion

    return all_documents

def procesar_compania_multi_fecha(nombre_compania, fechas, timestamp_extraccion):
    """Procesa una compañía descargando movimientos de múltiples fechas"""
    try:
        token, company_id = obtener_token_compania(nombre_compania)
        
        todos_movimientos = []
        for fecha in fechas:
            print(f"    → Descargando {fecha}...")
            movs = extraer_movimientos(nombre_compania, token, company_id, fecha, timestamp_extraccion)
            todos_movimientos.extend(movs)
        
        insertar_movimientos(todos_movimientos, nombre_compania)
        return {
            "compania": nombre_compania, 
            "status": "success", 
            "count": len(todos_movimientos),
            "fechas": fechas
        }
    except Exception as e:
        print(f"  ✗ [{nombre_compania}] Error: {e}")
        return {"compania": nombre_compania, "status": "error", "error": str(e)}



if __name__ == "__main__":
    from collections import defaultdict
    
    tiempo_inicio = datetime.now()
    
    print("\n" + "="*80)
    print("EXTRACCIÓN INTELIGENTE DE MOVIMIENTOS Y PIPELINE POR GRUPOS")
    print("="*80)
    
    # ========== PASO 1: ANALIZAR FECHAS NECESARIAS ==========
    fechas_por_compania = analizar_fechas_necesarias_por_grupo()
    
    if not fechas_por_compania:
        print("\n⚠️  No hay balances pendientes de procesar. Terminando.\n")
        exit(0)
    
    # ========== PASO 2: AGRUPAR COMPAÑÍAS POR GRUPO ==========
    companias_por_grupo = defaultdict(list)
    for compania, fechas in fechas_por_compania.items():
        # Encontrar a qué grupo pertenece
        for grupo, companias_grupo in GRUPOS_COMPANIAS.items():
            if compania in companias_grupo:
                companias_por_grupo[grupo].append((compania, fechas))
                break
    
    # Lista para acumular TODOS los resultados de pipeline
    todos_resultados = []
    
    # ========== PASO 3: PROCESAR CADA GRUPO ==========
    for grupo, companias_con_fechas in companias_por_grupo.items():
        print(f"\n{'='*80}")
        print(f"PROCESANDO GRUPO: {grupo}")
        print(f"Compañías: {len(companias_con_fechas)}")
        print(f"{'='*80}\n")
        
        # Timestamp ANTES de empezar la extracción del grupo
        timestamp_grupo = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"⏰ Timestamp de extracción del grupo: {timestamp_grupo}\n")
        
        # Ejecutar extracción en paralelo DENTRO del grupo
        resultados = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(procesar_compania_multi_fecha, compania, fechas, timestamp_grupo): compania 
                for compania, fechas in companias_con_fechas
            }
            
            for future in as_completed(futures):
                resultado = future.result()
                resultados.append(resultado)
                if resultado["status"] == "success":
                    fechas_str = ", ".join(resultado["fechas"])
                    print(f"  ✓ [{resultado['compania']}] {resultado['count']} movimientos ({fechas_str})")
                else:
                    print(f"  ✗ [{resultado['compania']}] Error")
        
        # Resumen de extracción del grupo
        exitosos = sum(1 for r in resultados if r["status"] == "success")
        fallidos = sum(1 for r in resultados if r["status"] == "error")
        total_movs = sum(r.get("count", 0) for r in resultados if r["status"] == "success")
        
        print(f"\n📊 RESUMEN EXTRACCIÓN {grupo}:")
        print(f"   ✓ Exitosos: {exitosos}/{len(companias_con_fechas)}")
        print(f"   ✗ Fallidos: {fallidos}")
        print(f"   📦 Total movimientos: {total_movs}")
        
        # EJECUTAR PIPELINE PARA ESTE GRUPO con su timestamp
        resultados_grupo = ejecutar_pipeline_grupo(grupo, timestamp_grupo)
        todos_resultados.extend(resultados_grupo)
        
        print(f"  ✓ Pipeline completada: {len(resultados_grupo)} balances procesados")
    
    # ========== PASO 4: EXPORTAR Y ENVIAR ==========
    print("\n" + "="*80)
    print("EXPORTACIÓN FINAL A GOOGLE SHEETS")
    print("="*80 + "\n")
    exportar_a_sheets(todos_resultados)
    
    # ENVIAR AL SISTEMA DE MONITOREO
    enviar_a_backend(todos_resultados, tiempo_inicio)
    
    print("\n✅ PROCESO COMPLETADO\n")

