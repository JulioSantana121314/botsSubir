import os
import time

scripts_folder = '.'

scripts = [
    'acebookBalance.py', # No Captcha
    'riversweepsBalance.py', # No Captcha
    'bluedragonBalance.py', # No Captcha
    'megaspinBalance.py', # No Captcha
    'glamourspinBalance.py', # No Captcha
    'fishgloryBalance.py', # No Captcha
    'vegasxBalance.py', # No Captcha
    'egameBalance.py', # No Captcha
    'goldentreasureBalance.py', # No Captcha
]

history_log = "runner_group3.log"

while True:
    duraciones = {}
    ciclo_inicio = time.strftime('%Y-%m-%d %H:%M:%S')
    print(f"\n=== Nuevo ciclo G3 iniciado {ciclo_inicio} ===")
    with open(history_log, "a", encoding="utf-8") as f:
        f.write(f"\n=== Ciclo iniciado {ciclo_inicio} ===\n")

    for script in scripts:
        script_path = os.path.join(scripts_folder, script)
        print(f"\n--- Ejecutando G3: {script} ---")
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
    print("\nResumen de duración por script (G3):")
    for script, duracion in duraciones.items():
        print(f"- {script}: {duracion:.1f} segundos")
    print(f"\nCiclo G3 terminado a las {ciclo_final}. Esperando 5 segundos para reiniciar...\n")
    with open(history_log, "a", encoding="utf-8") as f:
        f.write(f"=== Ciclo terminado {ciclo_final} ===\n")
    time.sleep(5)
