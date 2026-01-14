from pymongo import MongoClient, errors, UpdateOne
from dateutil import parser
from datetime import timedelta
import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv('MONGO_URI')
MONGO_DATABASE = "plataforma_finanzas"
MONGO_COLLECTION = "movimientos"

companies = {
    "Play Play Play": "650cbacb5b27367205467e2e",
    "Play OakCreek": "673676468f4b3a10e2b36f55",
    "Lucky Lady": "676de2098f4b3a10e2bfbde6",
    "Slap It": "67844482e2e1b941901a68f0",
    "Slot House": "6784494de2e1b941901a6aa1",
    "Slot Craze": "67844998e2e1b941901a6ac5",
    "Wise Gang": "67c08d2a6827e55261e7b238",
    "Game Room Sweeps": "67d83c4d4d4402d67e58c539",
    "Hailey Games": "67d84cd14d4402d67e58cc07",
    "KFGgames": "67daf0694d4402d67e5a34d6",
    "The Cash Cove": "6807d5fd0cf1a4579732a13e",
    "Macau Slots": "6807f45d0cf1a4579732b641",
    "Mushroom Kingdom": "6807f4e50cf1a4579732b68f",
    "WinStar": "6812379e0cf1a457973b409d",
    "Queen of Hearts": "6813f3380cf1a457973cfe37",
    "BitVegas": "68168e510cf1a457973fe58e",
    "Ballerz World of Gamez": "681ab4210cf1a4579743f3a3",
    "Ace Haven": "681dfecb0cf1a45797470fff",
    "Lucky Room": "683887aa76e73b576388d3f8",
    "Ocean Sluggerz": "68b0d37cb875bc1c2bd90274",
    "The Fun Room": "68d58c9ab875bc1c2bf3d613",
    "Ultra Lounge": "68f03872082e2ecbf0f99962",
    "Lucky Luxe": "68f29935082e2ecbf0fc47da",
    "Mega Ultra Win": "68f775e3d9dcfd88b92f7cdb",
    "Pandagod": "690b7ebc6afeb443becba72d",
    "The Players Lounge": "690bae996afeb443becbef82",
    "JLEnt": "68dff37c082e2ecbf0eb5e90",
    "Slots Gone Wild": "68f10fdc082e2ecbf0fa7d56",
    "Lucky Buddy": "68f8ec59686fdc02af8cc9b9",
    "Snarcade": "68f8d89a686fdc02af8cb8b9",
    "JJsreelsadventures": "68f180ea082e2ecbf0fafa2f",
    "Grabbin Cash": "6903e59beacdf563c72948fa",
    "BordersWay": "6904313eeacdf563c729bf82",
    "The Players Club": "6838884876e73b576388d479",
    "Devine Slots": "690018e9686fdc02af956c60",
    "Token Tiger": "68d6e9a9b875bc1c2bf4f81e",
    "Innercore Games": "6924a6deacc81a35ddf13ada",
    "Fast Fortunes" : "69065cf4eacdf563c72c5cf5",
}

SUPERADMIN_USER = os.getenv('SUPERADMIN_USER')
SUPERADMIN_PASS = os.getenv('SUPERADMIN_PASS')

def convertir_utc_a_utc5(iso_str):
    try:
        dt_utc = parser.isoparse(iso_str)
        dt_utc5 = dt_utc - timedelta(hours=5)
        return dt_utc5.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return ""  # Devuelve vacío si hay error de parseo

def insertar_movimientos(movimientos, nombre_compania):
    if not movimientos:
        print(f"No hay movimientos para insertar en {nombre_compania}.")
        return
    
    client = MongoClient(MONGODB_URI)
    db = client[MONGO_DATABASE]
    collection = db[MONGO_COLLECTION]
    
    try:
        bulk_ops = []
        
        for mov in movimientos:
            mov["company"] = nombre_compania
            if "updatedAt" in mov and mov["updatedAt"]:
                mov["updatedAt_utc5"] = convertir_utc_a_utc5(mov["updatedAt"])
            # El timestamp_extraccion ya viene en el movimiento
            
            # Upsert: si existe (_id match), actualiza TODO (incluyendo status)
            # Si no existe, lo inserta
            bulk_ops.append(
                UpdateOne(
                    {"_id": mov["_id"]},
                    {"$set": mov},
                    upsert=True
                )
            )
        
        result = collection.bulk_write(bulk_ops, ordered=False)
        
        insertados = result.upserted_count
        actualizados = result.modified_count
        sin_cambios = result.matched_count - result.modified_count
        
        print(f"  ✓ [{nombre_compania}] Nuevos: {insertados} | Actualizados: {actualizados} | Sin cambios: {sin_cambios}")
        
    except Exception as e:
        print(f"  ✗ Error en bulk_write para {nombre_compania}: {str(e)}")