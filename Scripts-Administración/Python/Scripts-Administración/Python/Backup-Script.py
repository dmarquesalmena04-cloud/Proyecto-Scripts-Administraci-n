'''
Análisis Arquitectónico y Decisiones de Diseño
1. ¿Por qué Python y no Bash (Linux) o PowerShell (Windows)?
Por qué se hizo así: Python ofrece una capa de abstracción estándar sobre el sistema operativo. Si hubiéramos usado Bash, el script habría fallado en Windows a menos que se instalara WSL. 
Si usábamos PowerShell, no funcionaría de forma nativa en la gran mayoría de distribuciones Linux sin dependencias adicionales. Python permite unificar la lógica de administración en un único archivo .py.
Porque no de otra forma: Escribir dos scripts separados (uno en Bash y otro en PowerShell) duplica el esfuerzo de mantenimiento, corrección de errores y documentación en tu portafolio.

2. Uso de pathlib en lugar de os.path
Por qué se hizo así: pathlib es la librería moderna de Python para la manipulación de rutas de archivos (introducida en Python 3.4). 
Maneja automáticamente las diferencias de barras (/ en Linux vs \ en Windows) sin que tengas que preocuparte por el sistema operativo anfitrión.
Porque no de otra forma: Las funciones tradicionales de os.path requieren concatenaciones manuales de strings y validaciones propensas a errores tipográficos según la plataforma.

3. Sello temporal con precisión de segundos (YYYYMMDD_HHMMSS)
Por qué se hizo así: Añadir un timestamp único garantiza que si ejecutas el script varias veces al día, las carpetas de respaldo anteriores nunca se sobrescriban. 
Esto es vital en entornos de producción para mantener un historial de versiones limpio.
'''

import os
import shutil
from datetime import datetime
from pathlib import Path

''' ↑↑↑
    |Importación de librerías nativas|
            import os: Permite interactuar con el sistema operativo (aunque su uso se reduce al mínimo gracias a pathlib).

            import shutil: Librería estándar especializada en operaciones de alto nivel sobre archivos y colecciones de archivos (copiar, mover, eliminar árboles enteros).

            from datetime import datetime: Se extrae la clase datetime para obtener la fecha y hora exacta del sistema en el momento de la ejecución.

            from pathlib import Path: Importa la clase orientada a objetos para manejar rutas de directorios y archivos de forma multiplataforma.
'''


'''
    |Definición de la función y normalización de rutas Python|
Se define una función limpia y modular que recibe el origen y el destino como cadenas de texto (str). Las anotaciones de tipo (: str) mejoran la legibilidad del código.
Path(origen).resolve() toma la ruta ingresada por el usuario (que puede ser relativa como ./datos o absoluta) y la convierte en una ruta absoluta canónica,
resolviendo cualquier ambigüedad en el sistema de archivos.
        ↓↓↓↓↓↓↓             ↓↓↓            ↓↓
'''
def realizar_backup(origen: str, destino: str):
    """
    Realiza una copia de seguridad de una carpeta de origen a un directorio de destino,
    añadiendo un sello temporal al nombre de la carpeta de respaldo.
    Compatible con Windows, Linux y macOS.
    """
    # Convertir rutas a objetos Path para compatibilidad multiplataforma absoluta
    ruta_origen = Path(origen).resolve()
    ruta_destino = Path(destino).resolve()
   
    ''' ↑↑↑↑↑
    |Validación de existencia y naturaleza del directorio de origen| 
    ruta_origen.exists(): Verifica preventivamente si la carpeta realmente existe en el disco duro para evitar excepciones fatales más adelante.
        
    ruta_origen.is_dir(): Asegura que la ruta apunte a un directorio y no a un archivo suelto (por ejemplo, un archivo de texto), 
        ya que la lógica de copiado recursivo está pensada para carpetas completas.
    '''

    # 1. Validar que la carpeta de origen exista y sea un directorio válido
    if not ruta_origen.exists():
        print(f"[ERROR] La ruta de origen no existe: {ruta_origen}")
        return False
    
    if not ruta_origen.is_dir():
        print(f"[ERROR] La ruta de origen especificada no es una carpeta: {ruta_origen}")
        return False

    # 2. Generar nombre único con fecha y hora (Ej: mi_carpeta_20261106_123000)
    '''
    Generación de nombres únicos y construcción de la ruta final
        datetime.now().strftime(...): Formatea la fecha actual. Por ejemplo, el 6 de noviembre de 2026 a las 12:42 PM generará la cadena 20261106_124200.

        ruta_origen.name: Extrae únicamente el nombre de la carpeta a respaldar (ej: si el origen es /home/user/documentos, extrae documentos).

         ruta_final_backup = ruta_destino / nombre_backup: Aquí pathlib brilla;
            el operador / concatena de manera segura la ruta de destino con el nuevo nombre de la carpeta, 
            adaptando automáticamente las barras separadoras al sistema operativo.
    
               ↓↓↓↓    
    '''
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre_backup = f"{ruta_origen.name}_{timestamp}"
    ruta_final_backup = ruta_destino / nombre_backup

    '''
     |Creación del contenedor de destino y ejecución del copiado|
        try:: Bloque de control de errores. Las operaciones de disco (lectura/escritura) son propensas a fallar por factores externos (permisos, falta de espacio).

        ruta_destino.mkdir(parents=True, exist_ok=True): Crea la carpeta de destino principal si no existe. 
                    parents=True crea los directorios intermedios necesarios (como un comando mkdir -p en Linux), y exist_ok=True evita que lance un error si la carpeta de destino ya existía previamente.

        shutil.copytree(origen, destino): Copia de forma recursiva todo el contenido de la carpeta de origen (subcarpetas y archivos) hacia la nueva ruta de respaldo.

        ↓↓↓↓↓↓
    '''
    try:
        # 3. Asegurar que el directorio de destino principal exista (crea padres si faltan)
        ruta_destino.mkdir(parents=True, exist_ok=True)
        
        print(f"[INFO] Iniciando backup de: {ruta_origen}")
        print(f"[INFO] Destino: {ruta_final_backup}")

        # 4. Copiar el árbol de directorios completo
        shutil.copytree(ruta_origen, ruta_final_backup)
        
        print(f"[EXITO] Backup completado exitosamente en: {ruta_final_backup}")
        return True

        '''
        |Manejo de excepciones específicas y control de flujo principal|
        
        except PermissionError: Captura específicamente errores de privilegios
          (muy común en Linux al intentar escribir en directorios protegidos sin sudo, o en Windows en carpetas de sistema).

        except Exception as e: Red de seguridad general para capturar cualquier otro imprevisto 
            (disco lleno, archivos bloqueados por otro proceso) mostrando el error exacto sin crashes abruptos.

        if __name__ == "__main__":: Estándar en Python que asegura que este bloque interactivo de consola solo se ejecute si el archivo es corrido directamente, 
            permitiendo que el script también pueda ser importado como módulo en otros proyectos futuros.

        .strip(): Elimina espacios en blanco accidentales que el usuario pueda dejar al copiar y pegar rutas en la terminal.
               ↓↓↓↓
        '''


    except PermissionError:
        print("[ERROR] Permiso denegado. Ejecute el script con privilegios de administrador/root.")
        return False
    except Exception as e:
        print(f"[ERROR] Ocurrió un error inesperado durante el respaldo: {e}")
        return False

if __name__ == "__main__":
    print("=== SCRIPT DE BACKUP AUTOMÁTICO MULTIPLATAFORMA ===")
    
    # Ejemplo de uso interactivo por consola
    origen_ingresado = input("Introduce la ruta de la carpeta que deseas respaldar: ").strip()
    destino_ingresado = input("Introduce la ruta de la carpeta de destino: ").strip()

    if origen_ingresado and destino_ingresado:
        realizar_backup(origen_ingresado, destino_ingresado)
    else:
        print("[ADVERTENCIA] Debes proporcionar rutas válidas.")