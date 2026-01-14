import pymongo
import gspread
from gspread.exceptions import WorksheetNotFound
from google.oauth2.service_account import Credentials
from datetime import datetime
from collections import defaultdict
import uuid

# --- MongoDB Config ---
MONGO_URI = "mongodb+srv://kam_db_user:VJbs7fgYKJokO9pz@cluster0.e8doyfk.mongodb.net/?appName=Cluster0"
MONGO_DB = "plataforma_finanzas"
COL_BALANCES = "balances_bot"

# --- Google Sheets Config ---
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SERVICE_ACCOUNT_FILE = "../credentials/bamboo-parsec-477706-i5-f024e2770bbe.json"
SPREADSHEET_ID = "1caBEqmk6sM6MJfiYyq5BX-Hu0r9BOj8lQtaONHIZWrc"
SHEET_NAME = "Balances"  # Mantenido por compatibilidad, pero no se usa

def crear_pipeline(grupo=None, timestamp_limite=None):
    """Crea la pipeline con filtros opcionales por grupo y timestamp"""
    
    # Match inicial
    match_stage = {"used_as_previous": False}
    
    # Agregar filtro por grupo si se especifica
    if grupo:
        match_stage["grupo"] = grupo
    
    # Agregar filtro por timestamp si se especifica
    if timestamp_limite:
        match_stage["fecha"] = {"$lte": timestamp_limite}
    
    pipeline = [
    {"$match": match_stage},
    {
        "$addFields": {
            "website_title": {
                "$reduce": {
                    "input": {
                        "$split": [
                            {"$toLower": {"$trim": {"input": "$website"}}},
                            " "
                        ]
                    },
                    "initialValue": "",
                    "in": {
                        "$concat": [
                            "$$value",
                            {"$cond": [{"$eq": ["$$value", ""]}, "", " "]},
                            {"$toUpper": {"$substrCP": ["$$this", 0, 1]}},
                            {
                                "$substrCP": [
                                    "$$this",
                                    1,
                                    {"$strLenCP": "$$this"}
                                ]
                            }
                        ]
                    }
                }
            }
        }
    },
    {"$sort": {"website_title": 1, "username": 1, "fecha": -1}},
    {
        "$group": {
            "_id": {"website": "$website_title", "username": "$username"},
            "balances": {
                "$push": {
                    "_id": "$_id",
                    "fecha": "$fecha",
                    "balance": "$balance",
                    "grupo": "$grupo",
                    "website": "$website_title"
                }
            }
        }
    },
    {
        "$project": {
            "website": "$_id.website",
            "username": "$_id.username",
            "grupo": {"$arrayElemAt": ["$balances.grupo", 0]},
            "fecha_actual": {"$arrayElemAt": ["$balances.fecha", 0]},
            "fecha_anterior": {"$arrayElemAt": ["$balances.fecha", 1]},
            "balance_actual": {"$arrayElemAt": ["$balances.balance", 0]},
            "balance_anterior": {"$arrayElemAt": ["$balances.balance", 1]}
        }
    },
    {
        "$addFields": {
            "fecha_actual_date": {"$toDate": "$fecha_actual"},
            "fecha_anterior_date": {"$toDate": "$fecha_anterior"},
            "website_norm": {"$toUpper": {"$trim": {"input": "$website"}}}
        }
    },
    {
        "$lookup": {
            "from": "grupos_companias",
            "let": {"grupo": "$grupo"},
            "pipeline": [
                {"$project": {"grupo": 1, "companias": 1, "_id": 0}},
                {"$match": {"$expr": {"$eq": ["$grupo", "$$grupo"]}}}
            ],
            "as": "grupo_companias_info"
        }
    },
    {
        "$addFields": {
            "companias": {
                "$cond": [
                    {"$gt": [{"$size": "$grupo_companias_info"}, 0]},
                    {"$arrayElemAt": ["$grupo_companias_info.companias", 0]},
                    []
                ]
            }
        }
    },
    {
        "$lookup": {
            "from": "movimientos",
            "let": {
                "website_norm": "$website_norm",
                "companias": "$companias",
                "fechaInicial": "$fecha_anterior_date",
                "fechaFinal": "$fecha_actual_date"
            },
            "pipeline": [
                {
                    "$addFields": {
                        "gameName_norm": {"$toUpper": {"$trim": {"input": "$gameName"}}},
                        "company_norm": {"$toUpper": {"$trim": {"input": "$company"}}},
                        "updatedAtUtc5": {"$toDate": "$updatedAt_utc5"}
                    }
                },
                {
                    "$match": {
                        "$expr": {
                            "$and": [
                                {"$eq": ["$gameName_norm", "$$website_norm"]},
                                {
                                    "$in": [
                                        "$company_norm",
                                        {
                                            "$map": {
                                                "input": "$$companias",
                                                "as": "c",
                                                "in": {"$toUpper": {"$trim": {"input": "$$c"}}}
                                            }
                                        }
                                    ]
                                },
                                {"$gte": ["$updatedAtUtc5", "$$fechaInicial"]},
                                {"$lte": ["$updatedAtUtc5", "$$fechaFinal"]},
                                {"$eq": ["$status", "Approved"]}
                            ]
                        }
                    }
                }
            ],
            "as": "movimientos_rango"
        }
    },
    {
        "$addFields": {
            "total_sum_add": {
                "$ifNull": [
                    {
                        "$sum": {
                            "$map": {
                                "input": {
                                    "$filter": {
                                        "input": "$movimientos_rango",
                                        "as": "mov",
                                        "cond": {"$eq": ["$$mov.type", "Add Credits"]}
                                    }
                                },
                                "as": "add",
                                "in": "$$add.amount"
                            }
                        }
                    },
                    0
                ]
            },
            "total_sum_withdraw": {
                "$ifNull": [
                    {
                        "$sum": {
                            "$map": {
                                "input": {
                                    "$filter": {
                                        "input": "$movimientos_rango",
                                        "as": "mov",
                                        "cond": {
                                            "$in": [
                                                "$$mov.type",
                                                ["Withdraw Credits", "Remove Credits"]
                                            ]
                                        }
                                    }
                                },
                                "as": "wd",
                                "in": "$$wd.amount"
                            }
                        }
                    },
                    0
                ]
            }
        }
    },
    {
        "$addFields": {
            "variacion_esperada": {
                "$cond": [
                    {"$gt": [{"$size": "$movimientos_rango"}, 0]},
                    {"$subtract": ["$total_sum_withdraw", "$total_sum_add"]},
                    0
                ]
            },
            "variacion_real": {
                "$cond": [
                    {
                        "$and": [
                            {"$ne": ["$balance_actual", None]},
                            {"$ne": ["$balance_anterior", None]}
                        ]
                    },
                    {"$subtract": ["$balance_actual", "$balance_anterior"]},
                    None
                ]
            }
        }
    },
    {
        "$addFields": {
            "diferencia_variacion": {
                "$cond": [
                    {
                        "$and": [
                            {"$ne": ["$variacion_esperada", None]},
                            {"$ne": ["$variacion_real", None]}
                        ]
                    },
                    {"$subtract": ["$variacion_real", "$variacion_esperada"]},
                    None
                ]
            }
        }
    },
    {
        "$project": {
            "website": 1,
            "username": 1,
            "grupo": 1,
            "companias": 1,
            "fecha_anterior": 1,
            "fecha_actual": 1,
            "balance_actual": 1,
            "balance_anterior": 1,
            "total_sum_add": 1,
            "total_sum_withdraw": 1,
            "variacion_esperada": 1,
            "variacion_real": 1,
            "diferencia_variacion": 1
        }
    }
]

    return pipeline

def ejecutar_pipeline_grupo(grupo, timestamp_grupo):
    """Ejecuta la pipeline para un grupo específico con su timestamp"""
    print(f"\n  📊 Procesando pipeline para grupo: {grupo}")
    print(f"  ⏰ Usando timestamp límite: {timestamp_grupo}")
    
    try:
        # Conectar a MongoDB
        client = pymongo.MongoClient(MONGO_URI)
        db = client[MONGO_DB]
        col_balances = db[COL_BALANCES]
        
        # Crear pipeline con filtros
        pipeline = crear_pipeline(grupo=grupo, timestamp_limite=timestamp_grupo)
        
        # Ejecutar pipeline
        print(f"  ⏳ Ejecutando pipeline...")
        results = list(col_balances.aggregate(pipeline, allowDiskUse=True))
        print(f"  ✓ Pipeline ejecutada: {len(results)} documentos para {grupo}")
        
        # ✅ MARCAR TODOS LOS BALANCES ENTRE ANTERIOR Y ACTUAL (EXCLUSIVO ACTUAL)
        if results:
            print(f"  ⏳ Marcando balances intermedios como usados...")
            balances_a_marcar = []
            
            for doc in results:
                website = doc["website"]
                username = doc["username"]
                fecha_anterior = doc.get("fecha_anterior")
                fecha_actual = doc.get("fecha_actual")
                
                # Si existe balance anterior, marcar todos desde anterior hasta antes del actual
                if fecha_anterior and fecha_actual:
                    # Buscar TODOS los balances en ese rango
                    balances_intermedios = col_balances.find({
                        "website": website,
                        "username": username,
                        "fecha": {
                            "$gte": fecha_anterior,  # Desde el anterior (inclusive)
                            "$lt": fecha_actual      # Hasta el actual (exclusive)
                        },
                        "used_as_previous": False
                    })
                    
                    for balance in balances_intermedios:
                        if balance["_id"] not in balances_a_marcar:
                            balances_a_marcar.append(balance["_id"])
            
            # Actualizar en bulk
            if balances_a_marcar:
                resultado_update = col_balances.update_many(
                    {"_id": {"$in": balances_a_marcar}},
                    {"$set": {"used_as_previous": True}}
                )
                print(f"  ✓ Marcados {resultado_update.modified_count} balances (anteriores e intermedios) como usados")
            else:
                print(f"  ℹ No hay balances para marcar (todos son balances iniciales)")
        
        return results
        
    except Exception as e:
        print(f"  ❌ Error en pipeline para {grupo}: {e}")
        import traceback
        traceback.print_exc()
        return []

def formatear_para_backend(todos_resultados):
    """
    Formatea los resultados al formato esperado por el frontend antiguo (main.js).
    Solo incluye registros con diferencias != 0 (robusto).
    Además fuerza un _id string URL-safe para evitar ids compuestos con comas/espacios.
    """
    def to_float(v):
        if v is None or v == "":
            return 0.0
        try:
            return float(v)
        except Exception:
            return 0.0

    records_con_diferencias = []

    for doc in todos_resultados:
        diff_num = to_float(doc.get("diferencia_variacion", None))

        # Filtrar 0 y casi-0 (temas de float)
        if abs(diff_num) < 1e-9:
            continue

        record = {
            # IMPORTANTE: estos son los campos que tu main.js viejo espera
            "_id": uuid.uuid4().hex,  # string sin espacios ni comas (URL-safe)
            "grupo": (doc.get("grupo") or "").strip(),
            "website": (doc.get("website") or "").strip(),
            "username": (doc.get("username") or "").strip(),

            "fechaAnterior": doc.get("fecha_anterior", ""),
            "fechaActual": doc.get("fecha_actual", ""),

            "balanceAnterior": doc.get("balance_anterior", 0),
            "balanceActual": doc.get("balance_actual", 0),

            "totalSumAdd": doc.get("total_sum_add", 0),
            "totalSumWithdraw": doc.get("total_sum_withdraw", 0),

            "variacionEsperada": doc.get("variacion_esperada", 0),
            "variacionReal": doc.get("variacion_real", 0),

            "diferenciaVariacion": diff_num,
        }

        records_con_diferencias.append(record)

    return records_con_diferencias

def enviar_a_backend(todos_resultados, tiempo_inicio):
    """
    Envía los resultados al sistema de monitoreo
    """
    import requests
    
    BACKEND_URL = 'https://biological-vanny-balance-monitor-8237935d.koyeb.app'
    
    # Formatear solo registros con diferencias
    records_con_diferencias = formatear_para_backend(todos_resultados)
    
    if not records_con_diferencias:
        print("\n📊 No hay registros con diferencias para enviar al sistema de monitoreo.")
        return None
    
    # Preparar payload
    duracion = int((datetime.now() - tiempo_inicio).total_seconds())
    payload = {
        "records": records_con_diferencias,
        "metadata": {
            "triggeredBy": "python-pipeline",
            "duration": duracion,
            "notes": f"Ejecución automática - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        }
    }
    
    print(f"\n{'='*80}")
    print("📤 ENVIANDO AL SISTEMA DE MONITOREO")
    print(f"{'='*80}")
    print(f"Total de registros procesados: {len(todos_resultados)}")
    print(f"Registros con diferencias: {len(records_con_diferencias)}")
    print(f"Duración de la pipeline: {duracion}s")
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/executions",
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 201:
            data = response.json()['data']
            execution_id = data['executionId']
            
            print(f"\n✅ EJECUCIÓN GUARDADA EXITOSAMENTE")
            print(f"{'='*80}")
            print(f"   ID de Ejecución: #{execution_id}")
            print(f"   Total de registros: {data['totalRecords']}")
            print(f"   Con diferencias: {data['recordsWithDiff']}")
            groups = data.get('groups', []) or []
            groups_str = ', '.join(str(g) for g in groups if g is not None and str(g).strip())
            if groups_str:
                print(f"   Grupos afectados: {groups_str}")
            else:
                print("   Grupos afectados: (sin datos)")            
            print(f"\n   📊 Ver en el dashboard: https://balance-monitor.pages.dev")
            print(f"{'='*80}\n")
            
            return execution_id
        else:
            print(f"\n⚠️ ERROR AL GUARDAR EN BACKEND")
            print(f"   Status Code: {response.status_code}")
            print(f"   Respuesta: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print(f"\n❌ NO SE PUDO CONECTAR CON EL BACKEND")
        print(f"   El servidor backend no está respondiendo en {BACKEND_URL}")
        print(f"   Verifica que el servicio esté activo")
        return None
    except requests.exceptions.Timeout:
        print(f"\n❌ TIMEOUT: El backend tardó demasiado en responder")
        return None
    except Exception as e:
        print(f"\n❌ ERROR INESPERADO: {e}")
        import traceback
        traceback.print_exc()
        return None

def exportar_a_sheets(todos_resultados):
    """
    Exporta resultados a Google Sheets, agrupando por grupo.
    Cada grupo se exporta a su propia hoja con el nombre del grupo.
    
    Mantiene el mismo nombre de función para compatibilidad con imports externos.
    """
    print("\n📊 EXPORTANDO RESULTADOS A GOOGLE SHEETS (POR GRUPO)")
    print("="*80)
    
    # Preparar headers
    headers = [
        "website",
        "username",
        "grupo",
        "fecha_actual",
        "balance_actual",
        "fecha_anterior",
        "balance_anterior",
        "total_sum_add",
        "total_sum_withdraw",
        "variacion_esperada",
        "variacion_real",
        "diferencia_variacion"
    ]
    
    try:
        # Agrupar resultados por grupo
        print("  ⏳ Agrupando resultados por grupo...")
        resultados_por_grupo = defaultdict(list)
        for doc in todos_resultados:
            grupo = doc.get("grupo", "Sin Grupo")
            if not grupo or not str(grupo).strip():
                grupo = "Sin Grupo"
            resultados_por_grupo[grupo].append(doc)
        
        print(f"  ✓ {len(resultados_por_grupo)} grupos detectados: {list(resultados_por_grupo.keys())}\n")
        
        # Conectar a Google Sheets
        print("  ⏳ Conectando a Google Sheets...")
        creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        gc = gspread.authorize(creds)
        sh = gc.open_by_key(SPREADSHEET_ID)
        print("  ✓ Conexión establecida\n")
        
        # Exportar cada grupo a su propia hoja
        total_exportados = 0
        for grupo, docs in resultados_por_grupo.items():
            nombre_hoja = str(grupo).strip()
            
            print(f"  🧾 Grupo: '{nombre_hoja}' | Registros: {len(docs)}")
            
            # Abrir o crear worksheet con el nombre del grupo
            try:
                worksheet = sh.worksheet(nombre_hoja)
                print(f"     ✓ Hoja existente encontrada")
            except WorksheetNotFound:
                worksheet = sh.add_worksheet(title=nombre_hoja, rows="2000", cols="20")
                print(f"     ✓ Nueva hoja creada")
            
            # Preparar filas para este grupo
            rows = []
            for doc in docs:
                rows.append([
                    doc.get("website", ""),
                    doc.get("username", ""),
                    doc.get("grupo", ""),
                    doc.get("fecha_actual", ""),
                    doc.get("balance_actual", ""),
                    doc.get("fecha_anterior", ""),
                    doc.get("balance_anterior", ""),
                    doc.get("total_sum_add", 0),
                    doc.get("total_sum_withdraw", 0),
                    doc.get("variacion_esperada", 0),
                    doc.get("variacion_real", 0),
                    doc.get("diferencia_variacion", 0)
                ])
            
            # Limpiar datos existentes (mantiene headers)
            worksheet.batch_clear(["A2:Z"])
            
            # Escribir headers y datos
            worksheet.update("A1", [headers])
            if rows:
                worksheet.update("A2", rows)
                total_exportados += len(rows)
            
            print(f"     ✓ Exportados {len(rows)} registros\n")
        
        print(f"✅ Exportación completada: {total_exportados} registros totales en {len(resultados_por_grupo)} hojas.\n")
        
    except Exception as e:
        print(f"\n❌ Error en exportación: {e}\n")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    tiempo_inicio = datetime.now()
    
    print("\n" + "="*80)
    print("🚀 INICIANDO PROCESAMIENTO DE BALANCES")
    print("="*80)
    
    # Conectar a MongoDB para obtener grupos
    client = pymongo.MongoClient(MONGO_URI)
    db = client[MONGO_DB]
    col_balances = db[COL_BALANCES]
    
    # Obtener grupos únicos
    timestamp_limite_global = None  # Cambiar si necesitas límite de fecha
    
    match = {"used_as_previous": False, "grupo": {"$ne": None, "$ne": ""}}
    if timestamp_limite_global:
        match["fecha"] = {"$lte": timestamp_limite_global}
    
    grupos = col_balances.distinct("grupo", match)
    grupos = [g for g in grupos if isinstance(g, str) and g.strip()]
    grupos.sort()
    
    print(f"\n📌 Grupos detectados: {grupos}\n")
    
    # Ejecutar pipeline para cada grupo y acumular todos los resultados
    todos_resultados = []
    
    for grupo in grupos:
        timestamp_grupo = timestamp_limite_global
        resultados = ejecutar_pipeline_grupo(grupo, timestamp_grupo)
        todos_resultados.extend(resultados)
    
    # Exportar todos los resultados (la función internamente los agrupa por grupo)
    exportar_a_sheets(todos_resultados)
    
    # Enviar al sistema de monitoreo
    enviar_a_backend(todos_resultados, tiempo_inicio)
    
    print("="*80)
    print("✅ PROCESO COMPLETADO")
    print("="*80 + "\n")
