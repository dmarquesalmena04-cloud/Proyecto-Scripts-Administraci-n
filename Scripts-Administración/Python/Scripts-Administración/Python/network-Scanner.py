import platform
import subprocess
import ipaddress
import socket
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

# Diccionario de servicios comunes y sus protocolos asociados
PUERTOS_COMUNES = {
    21: "FTP",
    22: "SSH",
    23: "Telnet",
    25: "SMTP",
    53: "DNS",
    80: "HTTP",
    443: "HTTPS",
    3306: "MySQL",
    3389: "RDP",
    8080: "HTTP-Proxy"
}

def estimar_sistema_operativo(ttl: int) -> str:
    """Estima el sistema operativo basándose en el valor TTL del paquete de respuesta."""
    if ttl is None:
        return "Desconocido"
    elif ttl <= 64:
        return "Linux / Unix / macOS"
    elif ttl <= 128:
        return "Windows"
    else:
        return "Dispositivo de Red / Otro (Cisco, etc.)"

def hacer_ping(ip: str) -> tuple[str, bool, str]:
    """
    Realiza un ping adaptado al SO, captura el TTL para determinar 
    el sistema operativo y verifica si el host está activo.
    """
    sistema = platform.system().lower()
    comando = ["ping", "-n", "1", "-w", "1000", ip] if sistema == "windows" else ["ping", "-c", "1", "-W", "1", ip]

    try:
        # Capturamos la salida estándar (stdout) para analizar el TTL
        resultado = subprocess.run(
            comando, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.DEVNULL, 
            text=True
        )
        
        if resultado.returncode == 0:
            # Buscar el patrón TTL=X o ttl=X en la respuesta del ping
            match = re.search(r'[Tt][Tt][Ll]=(\d+)', resultado.stdout)
            if match:
                ttl_valor = int(match.group(1))
                os_estimado = estimar_sistema_operativo(ttl_valor)
                return (ip, True, os_estimado)
            return (ip, True, "Desconocido")
            
    except Exception:
        pass
    
    return (ip, False, "Desconocido")

def obtener_banner(ip: str, puerto: int) -> str:
    """Intenta conectarse al puerto abierto y capturar el banner del servicio."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(2.0)
            s.connect((ip, puerto))
            if puerto in [80, 8080]:
                s.sendall(b"HEAD / HTTP/1.0\r\n\r\n")
            banner = s.recv(1024).decode('utf-8', errors='ignore').strip()
            if banner:
                return banner.split('\n')[0]
    except Exception:
        pass
    return "No disponible / Oculto"

def escanear_puerto(ip: str, puerto: int) -> tuple[int, str, str] | None:
    """Comprueba si un puerto específico está abierto y extrae su protocolo y versión."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1.0)
            resultado = s.connect_ex((ip, puerto))
            if resultado == 0:
                protocolo = PUERTOS_COMUNES.get(puerto, "Desconocido")
                version = obtener_banner(ip, puerto)
                return (puerto, protocolo, version)
    except Exception:
        pass
    return None

def escanear_host_completo(ip: str) -> dict:
    """Escanea los puertos comunes de un host activo y recopila sus servicios."""
    puertos_abiertos = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futuros = {executor.submit(escanear_puerto, ip, puerto): puerto for puerto in PUERTOS_COMUNES.keys()}
        for futuro in as_completed(futuros):
            res = futuro.result()
            if res:
                puerto, proto, version = res
                puertos_abiertos.append({
                    "puerto": puerto,
                    "protocolo": proto,
                    "version": version
                })
    return {"ip": ip, "puertos": puertos_abiertos}

def escanear_red(subred: str):
    """Escanea la subred usando barras de progreso visuales con tqdm."""
    try:
        net = ipaddress.ip_network(subred, strict=False)
    except ValueError as e:
        print(f"[ERROR] Subred inválida: {e}")
        return

    ips_a_escanear = [str(ip) for ip in net.hosts()]
    
    print(f"\n[INFO] Fase 1: Escaneando dispositivos en {subred}...")
    hosts_activos = []

    # ThreadPoolExecutor combinado con barra de progreso tqdm
    with ThreadPoolExecutor(max_workers=50) as executor:
        futuros = {executor.submit(hacer_ping, ip): ip for ip in ips_a_escanear}
        
        # tqdm muestra el progreso visual dinámicamente en la terminal
        with tqdm(total=len(ips_a_escanear), desc="Escaneando IPs", ncols=80) as pbar:
            for futuro in as_completed(futuros):
                ip, activo, sistema_op = futuro.result()
                if activo:
                    hosts_activos.append({"ip": ip, "os": sistema_op})
                pbar.update(1)

    print(f"\n[INFO] Se encontraron {len(hosts_activos)} dispositivos activos. Iniciando Fase 2 (Escaneo de puertos)...\n")
    
    resultados_globales = []
    for host in hosts_activos:
        print(f"[*] Analizando servicios en: {host['ip']} ({host['os']})...")
        info_puertos = escanear_host_completo(host['ip'])
        resultados_globales.append({
            "ip": host['ip'],
            "os": host['os'],
            "puertos": info_puertos['puertos']
        })

    # Informe final estructurado
    print("\n" + "="*60)
    print(" INFORME DE AUDITORÍA DE RED Y HUELLA DIGITAL (TTL)")
    print("="*60)
    for item in resultados_globales:
        print(f"\n Host IP: {item['ip']} | OS Estimado: {item['os']}")
        if not item['puertos']:
            print("   └─ No se encontraron puertos comunes abiertos.")
        else:
            for p in item['puertos']:
                print(f"   ├─ Puerto: {p['puerto']} ({p['protocolo']})")
                print(f"   │    └─ Versión: {p['version']}")
    print("="*60)

if __name__ == "__main__":
    print("=== ESCANER DE RED PRO MULTIPLATAFORMA ===")
    subred_ingresada = input("Introduce la subred a escanear (ej: 192.168.1.0/24): ").strip()
    if subred_ingresada:
        escanear_red(subred_ingresada)
    else:
        print("[ADVERTENCIA] Debes introducir una subred válida.")