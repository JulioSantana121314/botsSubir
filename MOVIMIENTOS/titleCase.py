from pymongo import MongoClient, UpdateOne

def to_title_case(s):
    if not s: return s
    return ' '.join([w.capitalize() for w in s.split()])

client = MongoClient(
    "mongodb+srv://kam_db_user:VJbs7fgYKJokO9pz@cluster0.e8doyfk.mongodb.net/?appName=Cluster0"
)
db = client["plataforma_finanzas"]
col = db["balances_bot"]

bulk_ops = []
for doc in col.find({}, {"_id": 1, "website": 1}):
    new_web = to_title_case(doc.get("website", ""))
    if new_web != doc.get("website", ""):
        bulk_ops.append(UpdateOne({'_id': doc['_id']}, {'$set': {'website': new_web}}))

if bulk_ops:
    result = col.bulk_write(bulk_ops)
    print(f"Actualizados: {result.modified_count}")
else:
    print("No hay cambios.")

client.close()
