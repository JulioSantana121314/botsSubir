from pymongo import MongoClient

GRUPOS_COMPANIAS = {
    "Tierlock": [
        "The Fun Room", "Slots Gone Wild", "JJsreelsadventures", "Lucky Luxe",
        "Snarcade", "Lucky Buddy", "Devine Slots", "BordersWay", "The Players Lounge", "Lucky Buddy"
    ],
    "TAP": ["JLEnt"],
    "PPP": ["Play Play Play", "Lucky Lady", "The Cash Cove"],
    "Wise Gang": ["Wise Gang", "Innercore Games", "Fast Fortunes"],
    "Ballerz": ["Ballerz World of Gamez"],
    "Slap It": ["Slap It"],
    "Oak Creek": ["Play OakCreek"],
    "Slap It y Oak Creek": ["Slap It", "Play OakCreek"],
    "Mushroom Kingdom": ["Mushroom Kingdom"],
    "Ocean Sluggerz": ["Ocean Sluggerz"],
    "Lucky Room": ["Lucky Room"],
    "Hailey Games": ["Hailey Games"],
    "Players Club": ["The Players Club"],
    "Pandagod" : ["Pandagod"],
    "Token Tiger" : ["Token Tiger"],
}

client = MongoClient("mongodb+srv://kam_db_user:VJbs7fgYKJokO9pz@cluster0.e8doyfk.mongodb.net/?appName=Cluster0")
db = client["plataforma_finanzas"]
col = db["grupos_companias"]

# Borrar todo lo anterior
col.delete_many({})
print("✅ Documentos anteriores eliminados")

# Insertar el diccionario nuevo
docs = [
    {"grupo": grupo, "companias": comps}
    for grupo, comps in GRUPOS_COMPANIAS.items()
]
result = col.insert_many(docs)
print(f"✅ {len(result.inserted_ids)} grupos insertados")

client.close()
