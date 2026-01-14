import pandas as pd

# Cambia por el nombre o ruta correcta de tu archivo
filename = "Estructura-2025.xlsx"

# Carga el archivo. Puedes ajustar sheet_name si no es la primera hoja
df = pd.read_excel(filename, sheet_name=0, header=1)

# Reemplaza por la lista de juegos tal y como aparecen en tu config.py
juegos = [
    "Orion Stars", "Fire kirin", "Panda Master", "Milky Way", "Vblink",
    "Ultra Panda", "Golden Treasure", "E Games", "Ace Book", "Juwa",
    "Game Vault", "HighStakes", "Galaxy World", "GameRoom",
    "Cash Machine", "Vegas Sweeps", "Mafia", "Noble", "Win Star",
    "Mr. All in one", "Lucky Stars", "Vegas X", "Mega Spin", "RiverSweeps",
    "100 Plus", "Cash Frenzy", "Blue Dragon", "Easy Street", "Fish Glory",
    "Gemini", "Glamour Spin", "High Roller", "Jackpot Frenzy", "Joker",
    "King of Pop", "Kraken", "Legend Fire", "Loot", "Moolah", "River Monster",
    "Sirius", "Super Dragon", "Vegas Roll", "Winner´s club", "Yolo", "Lucky Paradise 777"
]

# Emparejamiento fila a fila: usuario de una fila es tomado como username, la siguiente columna contiene password
websites = {}

for juego in juegos:
    # Intentar encontrar el nombre real de columna que contiene el juego
    column = None
    for col in df.columns:
        if isinstance(col, str) and juego.lower() in col.lower():
            column = col
            break
    if not column:
        continue

    accounts = []
    # Lee valores de la columna
    for val in df[column]:
        if pd.isna(val) or str(val).strip() == "-":
            continue
        username = str(val).strip()
        # Intenta buscar la contraseña en la fila correspondiente de la siguiente columna
        col_idx = df.columns.get_loc(column)
        password = None
        if col_idx + 1 < len(df.columns):
            password_val = df.iloc[accounts.__len__(), col_idx + 1]
            if not pd.isna(password_val) and str(password_val).strip() != "-":
                password = str(password_val).strip()

        accounts.append({"usuario": username, "password": password})

    # Puedes poner la URL de tu config directamente aquí, ejemplo por juego
    url_map = {
        "Orion Stars": "https://orionstars.vip:8781/default.aspx",
        # ...agrega las URLs de los demás juegos
    }
    if accounts:
        websites[juego.upper()] = {
            "url": url_map.get(juego, "CAMBIA ESTA URL"),
            "accounts": accounts
        }

import json
print(json.dumps(websites, ensure_ascii=False, indent=4))
