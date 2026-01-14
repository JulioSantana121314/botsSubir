import os
import time

# Carpeta donde están los scripts
scripts_folder = '.'

# Lista de scripts del grupo 2
scripts = [
    'cashfrenzyBalance.py', # Sí Captcha
    'winnersclubBalance.py', # Sí Captcha
    'superdragonBalance.py', # Sí Captcha
    'vegassweepsBalance.py', # Sí Captcha
    'highstakesBalance.py', # Sí Captcha
    'mrallinoneBalance.py', # Sí Captcha
    'siriusBalance.py', # Sí Captcha
    'easystreetBalance.py', # Sí Captcha
    'vegasrollBalance.py', # Sí Captcha
    'moolahBalance.py', # Sí Captcha
    'lootBalance.py', # Sí Captcha
    'luckyparadiseBalance.py', # Sí Captcha
    'rivermonsterBalance.py', # Sí Captcha
    'jokerBalance.py', # Sí Captcha
    'krakenBalance.py', # Sí Captcha
]

# Archivo de log histórico de este grupo
history_log = "runner_group2.log"

while True:
    duraciones = {}
    ciclo_inicio = time.strftime('%Y-%m-%d %H:%M:%S')
    print(f"\n=== Nuevo ciclo G2 iniciado {ciclo_inicio} ===")
    with open(history_log, "a", encoding="utf-8") as f:
        f.write(f"\n=== Ciclo iniciado {ciclo_inicio} ===\n")

    for script in scripts:
        script_path = os.path.join(scripts_folder, script)
        print(f"\n--- Ejecutando G2: {script} ---")
        start = time.time()
        exit_code = os.system(f'python "{script_path}"')
        end = time.time()
        duracion = end - start
        duraciones[script] = duracion
        msg = f"-- Terminó: {script} (exit code {exit_code}) | Tiempo: {duracion:.1f} segundos --"
        print(msg)
        with open(history_log, "a", encoding="utf-8") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} | {script} | {duracion:.1f} segundos | exit={exit_code}\n")

    ciclo_final = time.strftime('%Y-%m-%d %H:%M:%S')
    print("\nResumen de duración por script (G2):")
    for script, duracion in duraciones.items():
        print(f"- {script}: {duracion:.1f} segundos")
    print(f"\nCiclo G2 terminado a las {ciclo_final}. Esperando 5 segundos para reiniciar...\n")
    with open(history_log, "a", encoding="utf-8") as f:
        f.write(f"=== Ciclo terminado {ciclo_final} ===\n")
    time.sleep(5)
