import subprocess
import platform
import ipaddress

def hacer_ping(ip):
    parametro = "-n" if platform.system().lower() == "windows" else "-c"
    comando = ["ping", parametro, "1", "-w", "1000", str(ip)]
    
    resultado = subprocess.run(
        comando,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    return resultado.returncode == 0

def escanear_red(ruta_red):
    print(f"Escaneando red: {ruta_red}")
    red = ipaddress.ip_network(ruta_red, strict=False)
    
    activos = []
    for ip in red.hosts():
        if hacer_ping(ip):
            print(f"[ACTIVO] {ip}")
            activos.append(str(ip))
        else:
            print(f"[INACTIVO] {ip}", end="\r")
    
    print(f"\nDispositivos activos encontrados: {len(activos)}")
    return activos

if __name__ == "__main__":
    # Ejemplo: escanea tu red local (ajusta según tu IP real)
    escanear_red("192.168.1.0/24")