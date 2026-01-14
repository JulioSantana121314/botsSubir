import requests
from datetime import datetime, timedelta
from collections import defaultdict
import gspread
from google.oauth2.service_account import Credentials
from config import companies, SUPERADMIN_USER, SUPERADMIN_PASS


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

# Rango de fechas en UTC-5 (formato YYYY-MM-DD)
FECHA_INICIO = "2025-12-22"
FECHA_FIN = "2025-12-28"

# Google Sheets Config
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SERVICE_ACCOUNT_FILE = "../credentials/bamboo-parsec-477706-i5-f024e2770bbe.json"
SPREADSHEET_ID = "1VSQxeldFoJOjoaDt1IAI2j59UNSNlFN_fqYaQc-Xf6Q"
SHEET_NAME = "Daily"

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


def buscar_fila_fecha(worksheet, fecha_str):
    """
    Busca la fila donde está la fecha en columna A
    fecha_str: formato "D/M" (ej: "1/12")
    Retorna la fila donde está esa fecha
    """
    try:
        cell = worksheet.find(fecha_str, in_column=1)
        if cell:
            return cell.row
    except:
        pass
    return None


def escribir_tabla_wysaro(worksheet, fila_fecha, desglose_consolidado):
    """
    Escribe en la tabla WYSARO (columnas B:G)
    
    Si la tabla es B5:G17:
    - B5: header row (Platform, IN, OUT, HOLD, etc.)
    - B6:B17: nombres de plataformas
    - C6:C17: Add Credits (IN)
    - D6:D17: Remove Credits (OUT)
    """
    
    # Buscar la fila donde está "Platform" en columna B después de la fecha
    fila_header = None
    for offset in range(1, 15):  # Buscar hasta 15 filas después de la fecha
        try:
            test_cell = worksheet.cell(fila_fecha + offset, 2).value
            if test_cell == "Platform":
                fila_header = fila_fecha + offset
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
        
        if plataforma in desglose_consolidado:
            datos = desglose_consolidado[plataforma]
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


def generar_rango_fechas(fecha_inicio, fecha_fin):
    """
    Genera lista de fechas entre inicio y fin
    """
    inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d")
    fin = datetime.strptime(fecha_fin, "%Y-%m-%d")
    
    fechas = []
    fecha_actual = inicio
    while fecha_actual <= fin:
        fechas.append(fecha_actual.strftime("%Y-%m-%d"))
        fecha_actual += timedelta(days=1)
    
    return fechas


def formato_fecha_hoja(fecha_str):
    """
    Convierte YYYY-MM-DD a formato D/M
    Ejemplo: "2025-12-01" -> "1/12"
    """
    fecha = datetime.strptime(fecha_str, "%Y-%m-%d")
    return f"{fecha.day}/{fecha.month}"


if __name__ == "__main__":
    print("="*60)
    print("REPORTE DIARIO DE MOVIMIENTOS - WYSARO".center(60))
    print("="*60)
    print(f"\nRango UTC-5: {FECHA_INICIO} al {FECHA_FIN}\n")
    print(f"Compañías: {', '.join(COMPANIAS_WYSARO)}\n")
    print("="*60)
    
    # Conectar a Google Sheets
    print("\n--- Conectando a Google Sheets ---")
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SPREADSHEET_ID)
    worksheet = sh.worksheet(SHEET_NAME)
    print(f"✅ Conectado a hoja: {SHEET_NAME}")
    
    # Generar lista de fechas
    fechas = generar_rango_fechas(FECHA_INICIO, FECHA_FIN)
    
    # Procesar cada día
    for fecha_dia in fechas:
        fecha_formato_hoja = formato_fecha_hoja(fecha_dia)
        print(f"\n{'='*60}")
        print(f"Procesando: {fecha_formato_hoja} ({fecha_dia})".center(60))
        print(f"{'='*60}")
        
        # Buscar la fila de esta fecha en la hoja
        fila_fecha = buscar_fila_fecha(worksheet, fecha_formato_hoja)
        
        if not fila_fecha:
            print(f"⚠️  No se encontró la fecha {fecha_formato_hoja} en columna A")
            continue
        
        print(f"📍 Fecha encontrada en fila {fila_fecha}")
        
        # Acumulador para este día
        desglose_wysaro = defaultdict(lambda: {"IN": 0, "OUT": 0})
        
        # Procesar compañías WYSARO
        print(f"\n📊 Procesando compañías WYSARO...")
        for nombre_compania in COMPANIAS_WYSARO:
            if nombre_compania not in companies:
                print(f"  ⚠️ {nombre_compania} no existe en config")
                continue
            
            try:
                token, company_id = obtener_token_compania(nombre_compania)
                movimientos = extraer_movimientos_dia(nombre_compania, token, company_id, fecha_dia)
                
                if movimientos:
                    desglose = agrupar_por_plataforma(movimientos)
                    # Acumular en WYSARO
                    for plat, datos in desglose.items():
                        desglose_wysaro[plat]["IN"] += datos["IN"]
                        desglose_wysaro[plat]["OUT"] += datos["OUT"]
                    
                    print(f"  ✓ {nombre_compania}: {len(movimientos)} movimientos")
                else:
                    print(f"  - {nombre_compania}: sin movimientos")
                    
            except Exception as e:
                print(f"  ❌ {nombre_compania}: {e}")
        
        # Escribir en la tabla WYSARO
        print(f"\n📝 Escribiendo en Google Sheets...")
        escribir_tabla_wysaro(worksheet, fila_fecha, desglose_wysaro)
        
        print(f"✅ Día {fecha_formato_hoja} completado")
    
    print("\n" + "="*60)
    print("✓ Proceso completado para todos los días".center(60))
    print("="*60)
