import subprocess
import time
import os

GROUP_SCRIPTS = [
    "run_group1.py",
    "run_group2.py",
    # "run_group3.py",
    "run_group4.py",
]

HISTORY_LOG = "run_all_groups_history.log"

def main():
    procesos = {}
    tiempos_inicio = {}

    inicio_global = time.strftime('%Y-%m-%d %H:%M:%S')
    print(f"\n=== Lanzando todos los run_group a las {inicio_global} ===")

    with open(HISTORY_LOG, "a", encoding="utf-8") as f:
        f.write(f"\n=== Lanzando todos los run_group a las {inicio_global} ===\n")

    # Lanzar grupos
    for script in GROUP_SCRIPTS:
        if not os.path.exists(script):
            msg = f"[WARN] {script} no existe, se omite."
            print(msg)
            with open(HISTORY_LOG, "a", encoding="utf-8") as f:
                f.write(msg + "\n")
            continue
        print(f"Iniciando {script}...")
        p = subprocess.Popen(["python", script])
        procesos[script] = p
        tiempos_inicio[script] = time.time()

    print("\nTodos los grupos lanzados. Este script solo mide tiempos; no relanza nada.\n")
    with open(HISTORY_LOG, "a", encoding="utf-8") as f:
        f.write("Todos los grupos lanzados.\n")

    # Esperar a que terminen (si es que terminan)
    for script, p in procesos.items():
        p.wait()
        fin = time.time()
        duracion = fin - tiempos_inicio[script]
        msg = f"{script} terminó con código {p.returncode} | Duración: {duracion:.1f} segundos"
        print(msg)
        with open(HISTORY_LOG, "a", encoding="utf-8") as f:
            f.write(msg + "\n")

    fin_global = time.strftime('%Y-%m-%d %H:%M:%S')
    print(f"\n=== run_all_groups.py terminó a las {fin_global} ===")
    with open(HISTORY_LOG, "a", encoding="utf-8") as f:
        f.write(f"=== run_all_groups.py terminó a las {fin_global} ===\n")

if __name__ == "__main__":
    main()
