import requests
from datetime import datetime, timedelta
from collections import defaultdict
import gspread
from google.oauth2.service_account import Credentials
from config import companies, SUPERADMIN_USER, SUPERADMIN_PASS
import re


# ============================================================
# CONFIGURACIÓN - EDITA ESTOS VALORES
# ============================================================

# Compañías a evaluar para WYSARO
COMPANIAS_WYSARO = [
    "Token Tiger",
    "Fast Fortunes", 
    "Innercore Games",
    # Agrega todas las compañías que quieras incluir
]

# Google Sheets Config
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SERVICE_ACCOUNT_FILE = "../credentials/bamboo-parsec-477706-i5-f024e2770bbe.json"
SPREADSHEET_ID = "1VSQxeldFoJOjoaDt1IAI2j59UNSNlFN_fqYaQc-Xf6Q"
SHEET_NAME = "Weekly"  # Cambiar a la hoja que uses para rangos

# Lista de plataformas en orden
PLATAFORMAS_ORDEN = [
    "Ultra Panda",
    "Golden Dragon",
    "Vblink",
    "Panda Master",
    "Orion Stars",
    "Ace Book",
    "Golden Treasure",
    "Egames",
    "River Sweeps",
    "Game Vault",
    "Fire Kirin",
    "Juwa"
]

# ============================================================
# FIN DE CONFIGURACIÓN
# ============================================================


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


def extraer_movimientos_dia(nombre_compania, token, company_id, fecha_dia):
    """
    Extrae movimientos de un día específico
    fecha_dia: formato YYYY-MM-DD
    """
    headers = {"Authorization": f"Bearer {token}"}
    movements_url = "https://api.backend.biz/api/movements/paginated"
    page_size = 500

    date_filter = f"{fecha_dia},{fecha_dia}"
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

    all_documents = []
    for page in range(1, total_pages + 1):
        params["page"] = page
        resp = requests.get(movements_url, params=params, headers=headers)
        documents = resp.json().get("data", {}).get("documents", [])
        all_documents.extend(documents)

    return all_documents


def agrupar_por_plataforma(movimientos):
    """
    Agrupa movimientos por gameName y calcula IN y OUT
    SOLO considera movimientos con status "Approved"
    """
    desglose = defaultdict(lambda: {"IN": 0, "OUT": 0})
    
    for mov in movimientos:
        # FILTRO: Solo procesar si el status es "Approved"
        if mov.get("status") != "Approved":
            continue
            
        game_name = mov.get("gameName", "Sin Plataforma")
        amount = mov.get("amount", 0)
        mov_type = mov.get("type", "")
        
        if mov_type == "Add Credits":
            desglose[game_name]["IN"] += amount
        elif mov_type in ["Withdraw Credits", "Remove Credits"]:
            desglose[game_name]["OUT"] += amount
    
    return desglose


def parsear_rango_fecha(rango_str):
    """
    Parsea un rango de fecha del formato "1/12 - 7/12"
    Retorna (fecha_inicio_str, fecha_fin_str) en formato YYYY-MM-DD
    """
    # Regex para capturar "D/M - D/M" o "DD/MM - DD/MM"
    pattern = r'(\d{1,2})/(\d{1,2})\s*-\s*(\d{1,2})/(\d{1,2})'
    match = re.search(pattern, rango_str)
    
    if not match:
        return None, None
    
    dia_inicio, mes_inicio, dia_fin, mes_fin = match.groups()
    
    # Asumir año actual (2025)
    year = 2025
    
    fecha_inicio = f"{year}-{int(mes_inicio):02d}-{int(dia_inicio):02d}"
    fecha_fin = f"{year}-{int(mes_fin):02d}-{int(dia_fin):02d}"
    
    return fecha_inicio, fecha_fin


def generar_fechas_en_rango(fecha_inicio, fecha_fin):
    """
    Genera lista de fechas entre inicio y fin (inclusive)
    """
    inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d")
    fin = datetime.strptime(fecha_fin, "%Y-%m-%d")
    
    fechas = []
    fecha_actual = inicio
    while fecha_actual <= fin:
        fechas.append(fecha_actual.strftime("%Y-%m-%d"))
        fecha_actual += timedelta(days=1)
    
    return fechas


def buscar_rangos_fecha(worksheet):
    """
    Busca todos los rangos de fecha en columna A
    Retorna lista de tuplas: [(fila, rango_str, fecha_inicio, fecha_fin), ...]
    """
    # Obtener toda la columna A
    columna_a = worksheet.col_values(1)
    
    rangos = []
    pattern = r'\d{1,2}/\d{1,2}\s*-\s*\d{1,2}/\d{1,2}'
    
    for idx, valor in enumerate(columna_a):
        if valor and re.search(pattern, str(valor)):
            fila = idx + 1  # gspread usa 1-indexed
            fecha_inicio, fecha_fin = parsear_rango_fecha(valor)
            if fecha_inicio and fecha_fin:
                rangos.append((fila, valor, fecha_inicio, fecha_fin))
    
    return rangos


def escribir_tabla_wysaro(worksheet, fila_rango, desglose_wysaro):
    """
    Escribe en la tabla WYSARO (columnas B:G)
    
    Estructura:
    - B: Platform names (no tocar)
    - C: Add Credits (IN)
    - D: Remove Credits (OUT)
    """
    
    # Buscar la fila donde está "Platform" en columna B después del rango
    fila_header = None
    for offset in range(1, 15):  # Buscar hasta 15 filas después del rango
        try:
            test_cell = worksheet.cell(fila_rango + offset, 2).value  # Columna B = 2
            if test_cell == "Platform":
                fila_header = fila_rango + offset
                break
        except:
            pass
    
    if not fila_header:
        print(f"  ⚠️ No se encontró header 'Platform' en columna B")
        return None
    
    # Preparar actualizaciones en batch
    updates = []
    
    # Los datos empiezan en la fila siguiente al header
    fila_datos_inicio = fila_header + 1
    
    for idx, plataforma in enumerate(PLATAFORMAS_ORDEN):
        fila_actual = fila_datos_inicio + idx
        
        if plataforma in desglose_wysaro:
            datos = desglose_wysaro[plataforma]
            # Columna C: IN (Add Credits)
            updates.append({
                'range': f'C{fila_actual}',
                'values': [[datos["IN"]]]
            })
            # Columna D: OUT (Remove Credits)
            updates.append({
                'range': f'D{fila_actual}',
                'values': [[datos["OUT"]]]
            })
        else:
            # Si no hay datos, poner 0
            updates.append({
                'range': f'C{fila_actual}',
                'values': [[0]]
            })
            updates.append({
                'range': f'D{fila_actual}',
                'values': [[0]]
            })
    
    # Ejecutar batch update
    if updates:
        worksheet.batch_update(updates)
        print(f"  ✅ Tabla WYSARO actualizada en C{fila_datos_inicio}:D{fila_datos_inicio + len(PLATAFORMAS_ORDEN) - 1}")
    
    return fila_header


if __name__ == "__main__":
    print("="*60)
    print("REPORTE SEMANAL - WYSARO (RANGOS)".center(60))
    print("="*60)
    print(f"\nCompañías: {', '.join(COMPANIAS_WYSARO)}\n")
    print("="*60)
    
    # Conectar a Google Sheets
    print("\n--- Conectando a Google Sheets ---")
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SPREADSHEET_ID)
    worksheet = sh.worksheet(SHEET_NAME)
    print(f"✅ Conectado a hoja: {SHEET_NAME}")
    
    # Buscar todos los rangos de fecha en columna A
    print("\n--- Buscando rangos de fecha en columna A ---")
    rangos = buscar_rangos_fecha(worksheet)
    
    if not rangos:
        print("⚠️  No se encontraron rangos de fecha en columna A")
        exit()
    
    print(f"✅ Se encontraron {len(rangos)} rangos de fecha")
    
    # Procesar cada rango
    for fila_rango, rango_str, fecha_inicio, fecha_fin in rangos:
        print(f"\n{'='*60}")
        print(f"Procesando: {rango_str} (fila {fila_rango})".center(60))
        print(f"Rango: {fecha_inicio} al {fecha_fin}".center(60))
        print(f"{'='*60}")
        
        # Generar todas las fechas del rango
        fechas_rango = generar_fechas_en_rango(fecha_inicio, fecha_fin)
        print(f"📅 Procesando {len(fechas_rango)} días del rango")
        
        # Acumulador para todo el rango
        desglose_wysaro_rango = defaultdict(lambda: {"IN": 0, "OUT": 0})
        
        # Procesar todas las compañías WYSARO
        print(f"\n📊 Procesando compañías WYSARO...")
        for nombre_compania in COMPANIAS_WYSARO:
            if nombre_compania not in companies:
                print(f"  ⚠️ {nombre_compania} no existe en config")
                continue
            
            try:
                token, company_id = obtener_token_compania(nombre_compania)
                
                movimientos_compania = 0
                for fecha_dia in fechas_rango:
                    movimientos = extraer_movimientos_dia(nombre_compania, token, company_id, fecha_dia)
                    
                    if movimientos:
                        movimientos_compania += len(movimientos)
                        desglose_dia = agrupar_por_plataforma(movimientos)
                        # Acumular en el desglose del rango
                        for plat, datos in desglose_dia.items():
                            desglose_wysaro_rango[plat]["IN"] += datos["IN"]
                            desglose_wysaro_rango[plat]["OUT"] += datos["OUT"]
                
                if movimientos_compania > 0:
                    print(f"  ✓ {nombre_compania}: {movimientos_compania} movimientos totales")
                else:
                    print(f"  - {nombre_compania}: sin movimientos")
                    
            except Exception as e:
                print(f"  ❌ {nombre_compania}: {e}")
        
        # Escribir consolidado del rango en la tabla
        print(f"\n📝 Escribiendo consolidado del rango en Google Sheets...")
        escribir_tabla_wysaro(worksheet, fila_rango, desglose_wysaro_rango)
        
        print(f"✅ Rango {rango_str} completado")
    
    print("\n" + "="*60)
    print("✓ Proceso completado para todos los rangos".center(60))
    print("="*60)
