import platform
import psutil
import socket
import json
import subprocess
from datetime import datetime
from pathlib import Path

def obtener_tiempo_activo() -> str:
    """Calcula el tiempo que lleva el equipo encendido desde el último reinicio."""
    try:
        tiempo_boot = psutil.boot_time()
        tiempo_actual = datetime.now().timestamp()
        segundos_activos = int(tiempo_actual - tiempo_boot)
        
        dias = segundos_activos // 86400
        horas = (segundos_activos % 86400) // 3600
        minutos = (segundos_activos % 3600) // 60
        
        return f"{dias} días, {horas} horas, {minutos} minutos"
    except Exception:
        return "No disponible"

def comprobar_conectividad() -> bool:
    """Verifica si el equipo tiene salida a Internet conectándose a un DNS público (Cloudflare)."""
    try:
        # Intenta abrir un socket TCP al puerto 53 (DNS) de 1.1.1.1 con timeout de 2 segundos
        socket.setdefaulttimeout(2.0)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(("1.1.1.1", 53))
            return True
    except (socket.error, Exception):
        return False

def auditar_sistema() -> dict:
    """Recopila todas las métricas del sistema y construye un diccionario de auditoría."""
    print("[*] Iniciando auditoría integral del sistema...")
    
    # 1. Información General del SO
    info_so = {
        "sistema": platform.system(),
        "nodo": platform.node(),
        "release": platform.release(),
        "version": platform.version(),
        "arquitectura": platform.machine(),
        "procesador": platform.processor(),
        "tiempo_activo": obtener_tiempo_activo(),
        "conectividad_internet": comprobar_conectividad()
    }

    # 2. Rendimiento de Hardware (CPU y RAM)
    # interval=None para lectura rápida no bloqueante tras la primera llamada
    psutil.cpu_percent(interval=None)
    info_hardware = {
        "cpu_uso_porcentaje": psutil.cpu_percent(interval=1.0),
        "cpu_nucleos_fisicos": psutil.cpu_count(logical=False),
        "cpu_nucleos_totales": psutil.cpu_count(logical=True),
        "memoria_ram": {
            "total_gb": round(psutil.virtual_memory().total / (1024 ** 3), 2),
            "disponible_gb": round(psutil.virtual_memory().available / (1024 ** 3), 2),
            "usado_porcentaje": psutil.virtual_memory().percent
        }
    }

    # 3. Almacenamiento en Disco
    discos = []
    for particion in psutil.disk_partitions(all=False):
        try:
            uso = psutil.disk_usage(particion.mountpoint)
            discos.append({
                "dispositivo": particion.device,
                "punto_montaje": particion.mountpoint,
                "sistema_archivos": particion.fstype,
                "total_gb": round(uso.total / (1024 ** 3), 2),
                "usado_gb": round(uso.used / (1024 ** 3), 2),
                "libre_gb": round(uso.free / (1024 ** 3), 2),
                "porcentaje_uso": uso.percent
            })
        except PermissionError:
            continue

    # 4. Top 3 procesos con mayor consumo de CPU y RAM
    procesos = []
    for p in psutil.process_iter(['pid', 'name', 'username', 'memory_percent']):
        try:
            p.cpu_percent(interval=None)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    # Breve pausa para calcular CPU de procesos
    import time
    time.sleep(0.5)

    for p in psutil.process_iter(['pid', 'name', 'username', 'memory_percent']):
        try:
            info_p = p.info
            info_p['cpu_percent'] = p.cpu_percent(interval=None)
            if info_p['memory_percent'] is not None:
                procesos.append(info_p)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    top_cpu = sorted(procesos, key=lambda x: x['cpu_percent'], reverse=True)[:3]
    top_ram = sorted(procesos, key=lambda x: x['memory_percent'], reverse=True)[:3]

    # Consolidar reporte final
    reporte = {
        "timestamp_auditoria": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "sistema_operativo": info_so,
        "hardware": info_hardware,
        "almacenamiento": discos,
        "procesos_criticos": {
            "mayor_cpu": [{"pid": p['pid'], "nombre": p['name'], "cpu_pct": p['cpu_percent']} for p in top_cpu],
            "mayor_ram": [{"pid": p['pid'], "nombre": p['name'], "ram_pct": round(p['memory_percent'], 2)} for p in top_ram]
        }
    }
    
    return reporte

def guardar_reporte(reporte: dict):
    """Guarda el diccionario de auditoría en un archivo JSON con formato legible."""
    nombre_archivo = f"auditoria_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    ruta_salida = Path(nombre_archivo).resolve()
    
    with open(ruta_salida, 'w', encoding='utf-8') as f:
        json.dump(reporte, f, indent=4, ensure_ascii=False)
        
    print(f"\n[EXITO] Reporte de auditoría generado correctamente en:")
    print(f" 📂 {ruta_salida}")

if __name__ == "__main__":
    print("=" * 65)
    print(" 🛡️ AUDITOR INTEGRAL DE SISTEMAS Y GENERADOR DE REPORTES")
    print("=" * 65)
    
    try:
        datos_auditoria = auditar_sistema()
        guardar_reporte(datos_auditoria)
        
        # Determinar texto de conectividad visualmente
        estado_internet = "✅ Online" if datos_auditoria['sistema_operativo']['conectividad_internet'] else "❌ Offline"
        
        # Mostrar un resumen rápido por pantalla
        print("\n--- RESUMEN RÁPIDO ---")
        print(f" Host: {datos_auditoria['sistema_operativo']['nodo']}")
        print(f" OS: {datos_auditoria['sistema_operativo']['sistema']} {datos_auditoria['sistema_operativo']['release']}")
        print(f" CPU en Uso: {datos_auditoria['hardware']['cpu_uso_porcentaje']}%")
        print(f" RAM en Uso: {datos_auditoria['hardware']['memoria_ram']['usado_porcentaje']}%")
        print(f" Conectividad a Internet: {estado_internet}")
        
    except KeyboardInterrupt:
        print("\n[INFO] Auditoría cancelada por el usuario.")