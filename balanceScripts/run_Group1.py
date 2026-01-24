import os
import time

# Carpeta donde están los scripts
scripts_folder = '.'

# Lista de scripts del grupo 1
scripts = [
    'orionBalance.py', # Sí Captcha
    'gamevaultBalance.py', # Sí Captcha
    'pandamasterBalance.py', # Sí Captcha
    'juwaBalance.py', # Sí Captcha
    # 'kingofpopBalance.py', # Sí Captcha
    'firekirinBalance.py', # Sí Captcha
    'nobleBalance.py', # Sí Captcha
    'winstarBalance.py', # Sí Captcha
    'milkywayBalance.py', # Sí Captcha
    'cashmachineBalance.py', # Sí Captcha
    'galaxyworldBalance.py', # Sí Captcha
    'luckystarsBalance.py', # Sí Captcha
    'mafiaBalance.py', # Sí Captcha
    'gameroomBalance.py', # Sí Captcha
]

# Archivo de log histórico de este grupo
history_log = "runner_group1.log"

while True:
    duraciones = {}
    ciclo_inicio = time.strftime('%Y-%m-%d %H:%M:%S')
    print(f"\n=== Nuevo ciclo G1 iniciado {ciclo_inicio} ===")
    with open(history_log, "a", encoding="utf-8") as f:
        f.write(f"\n=== Ciclo iniciado {ciclo_inicio} ===\n")

    for script in scripts:
        script_path = os.path.join(scripts_folder, script)
        print(f"\n--- Ejecutando G1: {script} ---")
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
    print("\nResumen de duración por script (G1):")
    for script, duracion in duraciones.items():
        print(f"- {script}: {duracion:.1f} segundos")
    print(f"\nCiclo G1 terminado a las {ciclo_final}. Esperando 5 segundos para reiniciar...\n")
    with open(history_log, "a", encoding="utf-8") as f:
        f.write(f"=== Ciclo terminado {ciclo_final} ===\n")
    time.sleep(5)
