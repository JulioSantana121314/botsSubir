import os
import shutil
from pathlib import Path

# ✅ Configuración: Lista de carpetas origen
SOURCE_FOLDERS = [
    "../balanceScripts/captchas/GALAXY_WORLD",
    "../balanceScripts/captchas/GAME_VAULT",
    "../balanceScripts/captchas/HIGHSTAKES",
    "../balanceScripts/captchas/JUWA",
    "../balanceScripts/captchas/LOOT",
    "../balanceScripts/captchas/LUCKY_PARADISE",
    "../balanceScripts/captchas/SIRIUS",
    "../balanceScripts/captchas/VEGAS_SWEEPS",
]

DEST_FOLDER = "captcha_datasets/grupo3"  # Carpeta destino (dataset)

def copy_with_auto_rename(src_folders, dst_folder):
    """
    Copia archivos desde múltiples carpetas origen a una carpeta destino.
    Si el nombre existe, agrega _1, _2, _3, etc.
    Solo copia imágenes cuyo nombre base sea solo dígitos (sin letras).
    """
    os.makedirs(dst_folder, exist_ok=True)
    
    dst_path = Path(dst_folder)
    
    total_copied = 0
    total_renamed = 0
    total_skipped = 0
    
    for src_folder in src_folders:
        src_path = Path(src_folder)
        
        # Verificar si la carpeta existe
        if not src_path.exists():
            print(f"⚠️  Carpeta no encontrada: {src_folder}")
            continue
        
        print(f"\n{'='*60}")
        print(f"📁 Procesando: {src_folder}")
        print(f"{'='*60}")
        
        copied = 0
        renamed = 0
        skipped = 0
        
        for file in src_path.glob("*.*"):
            # Ignorar archivos que no son imágenes
            if file.suffix.lower() not in ['.png', '.jpg', '.jpeg']:
                continue
            
            # Obtener nombre base (sin contador ni extensión)
            base_name = file.stem
            
            # Si tiene _, tomar solo la parte antes del _
            if '_' in base_name:
                base_name = base_name.split('_')[0]
            
            # FILTRO: Solo aceptar si el nombre base es solo dígitos
            if not base_name.isdigit():
                skipped += 1
                print(f"   ⏭️  Ignorado (contiene letras): {file.name}")
                continue
            
            dest_file = dst_path / file.name
            
            # Si no existe, copiar directo
            if not dest_file.exists():
                shutil.copy2(file, dest_file)
                copied += 1
                print(f"   ✅ Copiado: {file.name}")
            else:
                # Si existe, buscar nombre disponible con _1, _2, etc.
                original_name = file.stem
                extension = file.suffix
                counter = 1
                
                while True:
                    new_name = f"{original_name}_{counter}{extension}"
                    new_dest = dst_path / new_name
                    
                    if not new_dest.exists():
                        shutil.copy2(file, new_dest)
                        renamed += 1
                        print(f"   🔄 Renombrado: {file.name} → {new_name}")
                        break
                    
                    counter += 1
        
        # Resumen por carpeta
        print(f"\n   Resumen {src_folder}:")
        print(f"   ✅ Copiados: {copied}")
        print(f"   🔄 Renombrados: {renamed}")
        print(f"   ⏭️  Ignorados: {skipped}")
        
        total_copied += copied
        total_renamed += renamed
        total_skipped += skipped
    
    # Resumen total
    print(f"\n{'='*60}")
    print(f"📊 RESUMEN TOTAL")
    print(f"{'='*60}")
    print(f"✅ Total copiados directamente: {total_copied}")
    print(f"🔄 Total renombrados (duplicados): {total_renamed}")
    print(f"⏭️  Total ignorados (con letras): {total_skipped}")
    print(f"📊 Total procesado: {total_copied + total_renamed}")
    print(f"📂 Carpetas procesadas: {len([f for f in SOURCE_FOLDERS if Path(f).exists()])}/{len(SOURCE_FOLDERS)}")
    print(f"{'='*60}")

if __name__ == "__main__":
    print("🔄 Copiando captchas desde múltiples carpetas...\n")
    copy_with_auto_rename(SOURCE_FOLDERS, DEST_FOLDER)
