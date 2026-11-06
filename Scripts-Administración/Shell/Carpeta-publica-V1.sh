'''
|Análisis Arquitectónico y Decisiones de Diseño|

    Bash como interfaz de control:
        Se usa Bash porque es el lenguaje nativo por excelencia en Linux para la automatización de tareas y la interacción directa con el sistema operativo y la red.

    Detección automática de IP (hostname -I):
        En lugar de obligar al usuario a buscar su propia dirección IP con ip a o ifconfig, el script la consulta automáticamente para mostrar la URL exacta de acceso.

    Servidor HTTP integrado en Python (-m http.server):
        En lugar de configurar un servidor web complejo, se aprovecha el módulo nativo de Python 3. Esto demuestra ingenio y conocimiento de los recursos que ya vienen "de serie" en los entornos modernos.

'''
#!/bin/bash

''' 
    1. Solicitar la ruta de la carpeta de manera interactiva 
        #!/bin/bash:
            Indica al sistema operativo que este archivo debe ejecutarse utilizando el intérprete de comandos Bash.
        echo "==================================================": 
            Imprime una línea divisoria estética en la terminal para separar visualmente la ejecución.
        read -p "..." CARPETA_PATH: 
            Muestra un mensaje al usuario (-p) pidiendo la ruta y guarda lo que el usuario escriba dentro de la variable personalizada llamada CARPETA_PATH.

'''
echo "=================================================="
read -p "Introduce la ruta completa de la carpeta a compartir: " CARPETA_PATH

# Validar que la carpeta exista
'''
    if [ ! -d "$CARPETA_PATH" ]; then:
        Evalúa una condición. El operador ! -d significa "si la ruta proporcionada no es un directorio existente".

    read -p ...:
         Si no existe, pregunta de forma interactiva si el usuario desea crearla.

    if [ "$CREAR" = "s" ] || [ "$CREAR" = "S" ]; then:
        Comprueba si la respuesta del usuario fue afirmativa (minúscula o mayúscula).

    mkdir -p "$CARPETA_PATH":
        Crea la carpeta solicitada. La bandera -p asegura que si hay carpetas intermedias faltantes en la ruta, las cree todas de golpe sin arrojar errores.

    else / exit 1:
         Si el usuario decide no crearla, imprime un mensaje de cancelación y exit 1 detiene inmediatamente la ejecución del script devolviendo un código de error al sistema.
'''
if [ ! -d "$CARPETA_PATH" ]; then
    read -p "La carpeta no existe. ¿Deseas crearla? (s/n): " CREAR
    if [ "$CREAR" = "s" ] || [ "$CREAR" = "S" ]; then
        mkdir -p "$CARPETA_PATH"
    else
        echo "Operación cancelada."
        exit 1
    fi
fi

# 2. Obtener la IP privada de tu máquina Linux en la red local

''' 
    hostname -I:
         Comando de Linux que devuelve todas las direcciones IP asignadas a las interfaces de red del equipo. awk  Toma el resultado anterior y, usando awk, extrae únicamente la primera IP de la lista (por si el equipo tiene múltiples tarjetas de red o interfaces virtuales). El resultado se almacena en IP_LOCAL.
    PUERTO=8000:
         Define una variable con el número de puerto estándar (8000) donde operará el servidor web local.
'''

IP_LOCAL=$(hostname -I | awk '{print $1}')

# Definir un puerto libre (el 8000 es el estándar para esto)
PUERTO=8000

# 3. Entrar a la carpeta elegida

'''
    cd "$CARPETA_PATH" || exit 1:
        Mueve la sesión de la terminal a la carpeta que se va a compartir. Si por alguna razón el cambio falla, el operador || exit 1 detiene el script por seguridad.

        Los comandos echo imprimen un panel informativo claro y amigable en la pantalla,
         combinando las variables IP_LOCAL y PUERTO para mostrarle al usuario la URL exacta que debe abrir
         en cualquier otro dispositivo (teléfono, tablet, otra PC) conectado a la misma red Wi-Fi.
'''

cd "$CARPETA_PATH" || exit 1

echo "=================================================="
echo " Cargando servidor web local..."
echo " Ruta compartida: $CARPETA_PATH"
echo "--------------------------------------------------"
echo " Cualquier dispositivo en tu Wi-Fi puede acceder desde el navegador en:"
echo " http://$IP_LOCAL:$PUERTO"
echo "=================================================="
echo "Presiona [CTRL + C] para detener el servidor y dejar de compartir."
echo "--------------------------------------------------"

# 4. Lanzar el servidor HTTP nativo de Python (funciona con Python 3)

#python3 -m http.server: Invoca al intérprete de Python 3 utilizando la bandera -m para ejecutar un módulo interno como si fuera un script independiente. En este caso, levanta un servidor HTTP ultraligero que comparte todos los archivos de la carpeta actual donde se posicionó el comando cd.
    #$PUERTO: Pasa la variable numérica (8000) para indicar en qué puerto debe escuchar las peticiones de red. Este proceso se queda bloqueado en la terminal mostrando las peticiones de acceso en tiempo real hasta que el usuario presiona [CTRL + C].

python3 -m http.server $PUERTO
