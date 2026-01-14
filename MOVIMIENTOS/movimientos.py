import requests
import logging
from datetime import datetime, timedelta
from collections import defaultdict
from dateutil import parser

print("✓ Script iniciado - imports OK")

# Intentar importar config
try:
    from config import companies, SUPERADMIN_USER, SUPERADMIN_PASS
    print(f"✓ Config importado OK - {len(companies)} compañías encontradas")
except Exception as e:
    print(f"✗ ERROR importando config: {e}")
    exit(1)

# ============================================================
# CONFIGURACIÓN: EDITA ESTAS FECHAS Y TOLERANCIA
# ============================================================
FECHA_INICIO = "2026-01-01"  # Formato YYYY-MM-DD
FECHA_FIN = "2026-01-07"     # Formato YYYY-MM-DD
TOLERANCIA_SEGUNDOS = 5      # ±5 segundos de tolerancia
# ============================================================

print(f"✓ Fechas configuradas: {FECHA_INICIO} al {FECHA_FIN}")
print(f"✓ Tolerancia: ±{TOLERANCIA_SEGUNDOS} segundos")

# Configurar logging
def setup_logging():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"duplicados_{ts}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler()
        ]
    )
    logging.info("="*100)
    logging.info("INICIO DEL PROCESO DE DETECCIÓN DE DUPLICADOS")
    logging.info("="*100)
    logging.info(f"Archivo de log: {log_file}")
    logging.info(f"Rango de fechas: {FECHA_INICIO} al {FECHA_FIN}")
    logging.info(f"Tolerancia de tiempo: ±{TOLERANCIA_SEGUNDOS} segundos")
    logging.info(f"Total de compañías a procesar: {len(companies)}")
    logging.info("="*100)
    return log_file


def parsear_fecha_iso(iso_str):
    """
    Convierte ISO string a datetime object
    """
    try:
        return parser.isoparse(iso_str)
    except Exception as e:
        logging.debug(f"Error parseando fecha '{iso_str}': {e}")
        return None


def obtener_token_compania(nombre_compania):
    logging.info(f"[{nombre_compania}] Iniciando autenticación...")
    
    login_url = "https://api.backend.biz/api/authentication/login/backend"
    login_data = {"username": SUPERADMIN_USER, "password": SUPERADMIN_PASS}
    
    resp = requests.post(login_url, json=login_data, timeout=30)
    resp.raise_for_status()
    super_token = resp.json()["data"]["token"]

    company_id = companies[nombre_compania]
    
    change_url = "https://api.backend.biz/api/authentication/change-company/master"
    headers = {"Authorization": f"Bearer {super_token}"}
    payload = {"companyId": company_id}
    
    cambio = requests.post(change_url, json=payload, headers=headers, timeout=30)
    cambio.raise_for_status()
    data = cambio.json()
    token = data.get("token") or data.get("data", {}).get("token")
    
    if not token:
        raise ValueError(f"No se pudo obtener token para {nombre_compania}: {data}")
    
    logging.info(f"[{nombre_compania}] ✓ Autenticación exitosa")
    return token, company_id


def extraer_movimientos_rango(nombre_compania, token, company_id, fecha_inicio, fecha_fin):
    logging.info(f"[{nombre_compania}] Extrayendo movimientos del rango {fecha_inicio} al {fecha_fin}...")
    
    headers = {"Authorization": f"Bearer {token}"}
    movements_url = "https://api.backend.biz/api/movements/paginated"
    page_size = 10000

    date_filter = f"{fecha_inicio},{fecha_fin}"
    params = {
        "filters": f'''[{{"type":"date","value":"{date_filter}"}},{{"type":"companyId","value":"{company_id}"}}]''',
        "page": 1,
        "pageSize": page_size,
        "timeZone": "America/Lima",
    }

    resp = requests.get(movements_url, params=params, headers=headers, timeout=60)
    resp.raise_for_status()
    json_data = resp.json()
    total_docs = json_data.get("data", {}).get("numberTotalDocuments", 0)
    total_pages = (total_docs // page_size) + (1 if total_docs % page_size else 0)
    
    logging.info(f"[{nombre_compania}] Total de documentos: {total_docs:,}")
    logging.info(f"[{nombre_compania}] Total de páginas: {total_pages}")

    if total_docs == 0:
        logging.warning(f"[{nombre_compania}] ⚠️  No hay movimientos en este rango")
        return []

    all_documents = []
    for page in range(1, total_pages + 1):
        params["page"] = page
        
        resp = requests.get(movements_url, params=params, headers=headers, timeout=60)
        resp.raise_for_status()
        documents = resp.json().get("data", {}).get("documents", [])
        all_documents.extend(documents)
        
        if page % 5 == 0 or page == total_pages:
            logging.info(f"[{nombre_compania}] Progreso: {page}/{total_pages} páginas | Acumulado: {len(all_documents):,}")

    logging.info(f"[{nombre_compania}] ✓ Descarga completada: {len(all_documents):,} movimientos totales")
    return all_documents


def detectar_duplicados(movimientos, tolerancia_segundos=5):
    """
    Detecta duplicados con mismo gameMobileId y createdAt dentro de ±tolerancia_segundos
    Solo considera duplicados si tienen _id distintos
    """
    logging.info(f"Analizando {len(movimientos):,} movimientos para detectar duplicados...")
    logging.info(f"Tolerancia: ±{tolerancia_segundos} segundos")
    
    # Preparar datos
    movimientos_validos = []
    sin_game_mobile_id = 0
    sin_created_at = 0
    sin_id = 0
    error_parse_fecha = 0
    
    for mov in movimientos:
        game_mobile_id = mov.get("gameMobileId", "")
        created_at_str = mov.get("createdAt", "")
        doc_id = mov.get("_id", "")
        
        if not game_mobile_id:
            sin_game_mobile_id += 1
            continue
        if not created_at_str:
            sin_created_at += 1
            continue
        if not doc_id:
            sin_id += 1
            continue
        
        # Parsear fecha
        created_at_dt = parsear_fecha_iso(created_at_str)
        if not created_at_dt:
            error_parse_fecha += 1
            continue
        
        movimientos_validos.append({
            "mov": mov,
            "gameMobileId": game_mobile_id,
            "createdAt_dt": created_at_dt,
            "createdAt_str": created_at_str,
            "_id": doc_id
        })
    
    if sin_game_mobile_id > 0:
        logging.warning(f"⚠️  {sin_game_mobile_id} movimientos sin gameMobileId (excluidos)")
    if sin_created_at > 0:
        logging.warning(f"⚠️  {sin_created_at} movimientos sin createdAt (excluidos)")
    if sin_id > 0:
        logging.warning(f"⚠️  {sin_id} movimientos sin _id (excluidos)")
    if error_parse_fecha > 0:
        logging.warning(f"⚠️  {error_parse_fecha} movimientos con error al parsear fecha (excluidos)")
    
    logging.info(f"Movimientos válidos para análisis: {len(movimientos_validos):,}")
    
    # Agrupar por gameMobileId primero
    por_game_id = defaultdict(list)
    for mv in movimientos_validos:
        por_game_id[mv["gameMobileId"]].append(mv)
    
    logging.info(f"gameMobileId únicos: {len(por_game_id):,}")
    
    # Para cada gameMobileId, buscar duplicados temporales
    grupos_duplicados = []
    total_comparaciones = 0
    
    for game_id, movs_list in por_game_id.items():
        if len(movs_list) < 2:
            continue  # No puede haber duplicados si solo hay 1
        
        # Ordenar por fecha para facilitar búsqueda
        movs_list.sort(key=lambda x: x["createdAt_dt"])
        
        # Comparar cada movimiento con los siguientes
        for i in range(len(movs_list)):
            grupo_temporal = [movs_list[i]]
            
            # Buscar otros movimientos dentro de la ventana de tiempo
            for j in range(i + 1, len(movs_list)):
                diff_segundos = abs((movs_list[j]["createdAt_dt"] - movs_list[i]["createdAt_dt"]).total_seconds())
                total_comparaciones += 1
                
                if diff_segundos <= tolerancia_segundos:
                    grupo_temporal.append(movs_list[j])
                else:
                    # Como está ordenado, si ya pasó la tolerancia, no hay más candidatos
                    break
            
            # Si hay 2+ movimientos en el grupo temporal, verificar si tienen _id distintos
            if len(grupo_temporal) >= 2:
                ids_unicos = set(m["_id"] for m in grupo_temporal)
                
                if len(ids_unicos) > 1:  # Solo si hay 2+ _id distintos
                    # Evitar duplicar el mismo grupo (marcar como procesado)
                    grupo_key = tuple(sorted([m["_id"] for m in grupo_temporal]))
                    
                    # Verificar si ya tenemos este grupo
                    if not any(tuple(sorted([m["_id"] for m in g])) == grupo_key for g in grupos_duplicados):
                        grupos_duplicados.append(grupo_temporal)
    
    logging.info(f"Total de comparaciones realizadas: {total_comparaciones:,}")
    logging.info(f"✓ Análisis completado")
    logging.info(f"  - Grupos con duplicados (distinto _id, ±{tolerancia_segundos}s): {len(grupos_duplicados):,}")
    
    total_movs_duplicados = sum(len(g) for g in grupos_duplicados)
    logging.info(f"  - Total de movimientos duplicados: {total_movs_duplicados:,}")
    
    return grupos_duplicados


def mostrar_duplicados(grupos_duplicados):
    if not grupos_duplicados:
        logging.info("✅ No se encontraron movimientos duplicados")
        print("\n✅ No se encontraron movimientos duplicados")
        return
    
    print(f"\n{'='*120}")
    print(f"🔍 RESUMEN DE DUPLICADOS".center(120))
    print(f"{'='*120}")
    print(f"Total de grupos duplicados: {len(grupos_duplicados):,}")
    print(f"Total de movimientos afectados: {sum(len(g) for g in grupos_duplicados):,}")
    print(f"{'='*120}\n")
    
    # Solo mostrar primeros 20 grupos en consola
    max_mostrar = 20
    for idx, grupo in enumerate(grupos_duplicados[:max_mostrar], 1):
        game_id = grupo[0]["gameMobileId"]
        ids_unicos = set(m["_id"] for m in grupo)
        
        # Calcular diferencia temporal máxima en el grupo
        fechas = [m["createdAt_dt"] for m in grupo]
        diff_max = (max(fechas) - min(fechas)).total_seconds()
        
        header = f"[Grupo #{idx}] gameMobileId: {game_id}"
        print(f"\n{header}")
        print(f"  IDs únicos: {len(ids_unicos)} | Total movimientos: {len(grupo)} | Diferencia temporal máx: {diff_max:.2f}s")
        print("-"*120)
        
        for i, mv in enumerate(grupo, 1):
            mov = mv["mov"]
            info = (
                f"  [{i}] _id: {mv['_id']} | "
                f"createdAt: {mv['createdAt_str']} | "
                f"Company: {mov.get('company', 'N/A')} | "
                f"Type: {mov.get('type', 'N/A')} | "
                f"Amount: {mov.get('amount', 'N/A')} | "
                f"Status: {mov.get('status', 'N/A')}"
            )
            print(info)
    
    if len(grupos_duplicados) > max_mostrar:
        print(f"\n... y {len(grupos_duplicados) - max_mostrar} grupos más (ver CSV completo)")


def exportar_duplicados_csv(grupos_duplicados, filename=None):
    if not grupos_duplicados:
        return
    
    if filename is None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"duplicados_{ts}.csv"
    
    logging.info(f"Exportando duplicados a CSV: {filename}")
    
    import csv
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'grupo_num', 'gameMobileId', 'diferencia_temporal_max_segundos', 
            'dup_num', '_id', 'createdAt', 'company', 'type', 'amount', 'status', 
            'customerUsername', 'customerEmail', 'gameName', 'updatedAt'
        ])
        
        rows_written = 0
        for grupo_idx, grupo in enumerate(grupos_duplicados, 1):
            game_id = grupo[0]["gameMobileId"]
            
            # Calcular diferencia temporal
            fechas = [m["createdAt_dt"] for m in grupo]
            diff_max = (max(fechas) - min(fechas)).total_seconds()
            
            for dup_idx, mv in enumerate(grupo, 1):
                mov = mv["mov"]
                writer.writerow([
                    grupo_idx,
                    game_id,
                    f"{diff_max:.2f}",
                    dup_idx,
                    mv["_id"],
                    mv["createdAt_str"],
                    mov.get('company', ''),
                    mov.get('type', ''),
                    mov.get('amount', ''),
                    mov.get('status', ''),
                    mov.get('customerUsername', ''),
                    mov.get('customerEmail', ''),
                    mov.get('gameName', ''),
                    mov.get('updatedAt', '')
                ])
                rows_written += 1
    
    logging.info(f"✓ CSV exportado: {filename} ({rows_written:,} filas)")
    print(f"\n📄 Duplicados exportados a: {filename}")


if __name__ == "__main__":
    print("\n" + "="*120)
    print("INICIANDO DETECCIÓN DE DUPLICADOS".center(120))
    print("="*120)
    
    try:
        log_file = setup_logging()
        print(f"✓ Logging configurado: {log_file}")
    except Exception as e:
        print(f"✗ ERROR configurando logging: {e}")
        exit(1)
    
    # Validar fechas
    try:
        datetime.strptime(FECHA_INICIO, "%Y-%m-%d")
        datetime.strptime(FECHA_FIN, "%Y-%m-%d")
        print(f"✓ Fechas validadas OK")
    except ValueError as e:
        logging.error(f"❌ Formato de fecha inválido: {e}")
        print(f"❌ Formato de fecha inválido. Usa YYYY-MM-DD.")
        exit(1)
    
    # Descargar movimientos
    todos_movimientos = []
    companias_exitosas = 0
    companias_fallidas = 0
    
    print(f"\n{'='*120}")
    print(f"FASE 1: DESCARGANDO MOVIMIENTOS DE {len(companies)} COMPAÑÍAS".center(120))
    print(f"{'='*120}\n")
    
    for idx, nombre_compania in enumerate(companies.keys(), 1):
        print(f"[{idx}/{len(companies)}] Procesando: {nombre_compania}...", end=" ", flush=True)
        
        try:
            token, company_id = obtener_token_compania(nombre_compania)
            movimientos = extraer_movimientos_rango(
                nombre_compania, token, company_id, FECHA_INICIO, FECHA_FIN
            )
            
            for mov in movimientos:
                mov["company"] = nombre_compania
            
            todos_movimientos.extend(movimientos)
            companias_exitosas += 1
            
            print(f"✓ {len(movimientos):,} movimientos")
            
        except Exception as e:
            companias_fallidas += 1
            print(f"✗ Error: {str(e)[:80]}")
            logging.error(f"[{nombre_compania}] Error completo:", exc_info=True)
    
    print(f"\n{'='*120}")
    print(f"RESUMEN DE DESCARGA".center(120))
    print(f"{'='*120}")
    print(f"Compañías exitosas: {companias_exitosas}/{len(companies)}")
    print(f"Compañías con errores: {companias_fallidas}/{len(companies)}")
    print(f"Total movimientos descargados: {len(todos_movimientos):,}")
    print(f"{'='*120}")
    
    if len(todos_movimientos) == 0:
        print("\n⚠️  No hay movimientos para analizar. Finalizando.")
        logging.warning("No hay movimientos para analizar")
        exit(0)
    
    # Detectar duplicados
    print(f"\n{'='*120}")
    print(f"FASE 2: ANALIZANDO DUPLICADOS (±{TOLERANCIA_SEGUNDOS}s, _id distintos)".center(120))
    print(f"{'='*120}\n")
    
    grupos_duplicados = detectar_duplicados(todos_movimientos, TOLERANCIA_SEGUNDOS)
    
    # Mostrar resultados
    mostrar_duplicados(grupos_duplicados)
    
    # Exportar a CSV
    if grupos_duplicados:
        exportar_duplicados_csv(grupos_duplicados)
    
    print(f"\n{'='*120}")
    print("✓ PROCESO COMPLETADO".center(120))
    print(f"{'='*120}\n")
    
    logging.info("✓ PROCESO COMPLETADO")
