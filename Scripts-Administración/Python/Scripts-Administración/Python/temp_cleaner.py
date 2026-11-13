import os
import time
import platform
from pathlib import Path

def obtener_carpetas_tipicas() -> list[Path]:
    """Detecta el sistema operativo y devuelve las rutas temporales y de logs más comunes."""
    sistema = platform.system().lower()
    carpetas = []
    
    if sistema == "windows":
        # Obtener la variable de entorno USERPROFILE o APPDATA
        user_profile = Path(os.environ.get("USERPROFILE", "C:\\"))
        windir = Path(os.environ.get("WINDIR", "C:\\Windows"))
        
        tmp_local = user_profile / "AppData" / "Local" / "Temp"
        windows_temp = windir / "Temp"
        
        if tmp_local.exists(): carpetas.append(tmp_local)
        if windows_temp.exists(): carpetas.append(windows_temp)
        
    elif sistema in ["linux", "darwin"]: # Linux o macOS
        carpetas.append(Path("/tmp"))
        carpetas.append(Path("/var/tmp"))
        
        # Si es Linux, añadir opcionalmente la carpeta de logs del usuario si existe
        if sistema == "linux":
            log_user = Path.home() / ".local" / "share"
            if log_user.exists():
                carpetas.append(log_user)
                
    return carpetas

def limpiar_directorio(ruta_base: Path, dias_antiguedad: int = 7) -> tuple[int, int]:
    """Limpia archivos temporales y logs antiguos en un directorio dado de forma recursiva."""
    if not ruta_base.exists() or not ruta_base.is_dir():
        return 0, 0

    tiempo_actual = time.time()
    segundos_limite = dias_antiguedad * 86400  # 86400 segundos = 1 día
    
    archivos_borrados = 0
    espacio_liberado_bytes = 0
    extensiones_basura = {".tmp", ".log", ".bak", ".old", ".swp", ".dmp"}

    for ruta_archivo in ruta_base.rglob("*"):
        try:
            if ruta_archivo.is_file() and ruta_archivo.suffix.lower() in extensiones_basura:
                tiempo_modificacion = ruta_archivo.stat().st_mtime
                edad_archivo_segundos = tiempo_actual - tiempo_modificacion

                # Borrar si supera los días de inactividad establecidos (por defecto 7 días)
                if edad_archivo_segundos > segundos_limite:
                    tamanio = ruta_archivo.stat().st_size
                    try:
                        ruta_archivo.unlink()
                        archivos_borrados += 1
                        espacio_liberado_bytes += tamanio
                    except PermissionError:
                        # Archivos bloqueados por procesos en ejecución se ignoran silenciosamente
                        continue
                    except Exception:
                        continue
        except Exception:
            continue

    return archivos_borrados, espacio_liberado_bytes

def ejecutar_limpieza_automatica():
    """Ejecuta el proceso de limpieza automático en las rutas típicas del sistema."""
    print("=" * 60)
    print(f" 🤖 MANTENIMIENTO AUTOMÁTICO DE SISTEMA ({platform.system()})")
    print("=" * 60)
    
    rutas_a_limpiar = obtener_carpetas_tipicas()
    
    if not rutas_a_limpiar:
        print("[AVISO] No se encontraron rutas temporales estándar para escanear.")
        return

    total_archivos = 0
    total_bytes = 0

    for carpeta in rutas_a_limpiar:
        print(f"[INFO] Analizando y limpiando: {carpeta}...")
        borrados, bytes_lib = limpiar_directorio(carpeta, dias_antiguedad=7)
        total_archivos += borrados
        total_bytes += bytes_lib

    espacio_mb = total_bytes / (1024 ** 2)

    print("\n" + "=" * 60)
    print(" RESUMEN DE LIMPIEZA AUTOMÁTICA")
    print("=" * 60)
    print(f" Total de archivos basura eliminados: {total_archivos}")
    print(f" Espacio total liberado en disco: {espacio_mb:.2f} MB")
    print("=" * 60)
    print("[EXITO] Proceso de mantenimiento finalizado correctamente.")

if __name__ == "__main__":
    ejecutar_limpieza_automatica()