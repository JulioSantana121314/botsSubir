import sys
from pathlib import Path
import requests
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from config import companies, SUPERADMIN_USER, SUPERADMIN_PASS, insertar_movimientos

# Solo diccionario está en la carpeta anterior
sys.path.insert(0, str(Path(__file__).parent.parent))
from diccionario import GRUPOS_COMPANIAS

# Importar las nuevas funciones de pipeline
from pipeline_balances import ejecutar_pipeline_grupo, exportar_a_sheets, enviar_a_backend

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

def extraer_movimientos(nombre_compania, token, company_id, timestamp_extraccion):
    headers = {"Authorization": f"Bearer {token}"}
    movements_url = "https://api.backend.biz/api/movements/paginated"
    page_size = 500

    today = datetime.now().strftime("%Y-%m-%d")
    date_filter = f"{today},{today}"

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

def procesar_compania(nombre_compania, timestamp_extraccion):
    """Procesa una compañía: obtiene token, extrae movimientos e inserta en MongoDB"""
    try:
        token, company_id = obtener_token_compania(nombre_compania)
        movimientos = extraer_movimientos(nombre_compania, token, company_id, timestamp_extraccion)
        insertar_movimientos(movimientos, nombre_compania)
        return {"compania": nombre_compania, "status": "success", "count": len(movimientos)}
    except Exception as e:
        print(f"  ✗ [{nombre_compania}] Error: {e}")
        return {"compania": nombre_compania, "status": "error", "error": str(e)}

if __name__ == "__main__":
    tiempo_inicio = datetime.now()
    
    print("\n" + "="*80)
    print("EXTRACCIÓN DE MOVIMIENTOS Y PIPELINE POR GRUPOS")
    print("="*80)
    
    # Lista para acumular TODOS los resultados de pipeline
    todos_resultados = []

    # Procesar cada grupo secuencialmente
    for grupo, companias_grupo in GRUPOS_COMPANIAS.items():
        print(f"\n{'='*80}")
        print(f"PROCESANDO GRUPO: {grupo}")
        print(f"Compañías: {', '.join(companias_grupo)}")
        print(f"{'='*80}\n")
        
        # Filtrar solo las que existen en companies
        companias_validas = [c for c in companias_grupo if c in companies]
        companias_invalidas = [c for c in companias_grupo if c not in companies]
        
        if companias_invalidas:
            print(f"⚠ Compañías no encontradas en config: {', '.join(companias_invalidas)}\n")
        
        if not companias_validas:
            print(f"✗ No hay compañías válidas para procesar en {grupo}\n")
            continue
        
        # Timestamp ANTES de empezar la extracción del grupo
        timestamp_grupo = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"⏰ Timestamp de extracción del grupo: {timestamp_grupo}\n")
        
        # Ejecutar extracción en paralelo DENTRO del grupo
        resultados = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(procesar_compania, nombre, timestamp_grupo): nombre 
                for nombre in companias_validas
            }
            
            for future in as_completed(futures):
                resultado = future.result()
                resultados.append(resultado)
                if resultado["status"] == "success":
                    print(f"  ✓ [{resultado['compania']}] Completado: {resultado['count']} movimientos")
                else:
                    print(f"  ✗ [{resultado['compania']}] Error")
        
        # Resumen de extracción del grupo
        exitosos = sum(1 for r in resultados if r["status"] == "success")
        fallidos = sum(1 for r in resultados if r["status"] == "error")
        total_movs = sum(r.get("count", 0) for r in resultados if r["status"] == "success")
        
        print(f"\n📊 RESUMEN EXTRACCIÓN {grupo}:")
        print(f"   ✓ Exitosos: {exitosos}/{len(companias_validas)}")
        print(f"   ✗ Fallidos: {fallidos}")
        print(f"   📦 Total movimientos: {total_movs}")
        
        # EJECUTAR PIPELINE PARA ESTE GRUPO con su timestamp
        resultados_grupo = ejecutar_pipeline_grupo(grupo, timestamp_grupo)
        todos_resultados.extend(resultados_grupo)
        
        print(f"  ✓ Pipeline completada: {len(resultados_grupo)} balances procesados")

    # EXPORTAR TODO A SHEETS al final
    print("\n" + "="*80)
    print("EXPORTACIÓN FINAL A GOOGLE SHEETS")
    print("="*80 + "\n")
    exportar_a_sheets(todos_resultados)
    
    # ENVIAR AL SISTEMA DE MONITOREO
    enviar_a_backend(todos_resultados, tiempo_inicio)
    
    print("\n✅ PROCESO COMPLETADO\n")
