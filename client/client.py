actions_route = 'actions.txt'


def leer_archivo_txt(ruta_archivo):
    try:
        with open(ruta_archivo, 'r', encoding='utf-8') as archivo:
            lineas = archivo.readlines()
            lineas = [linea.strip() for linea in lineas if linea.strip()]  # Eliminar saltos de línea y líneas vacías
            return lineas
    except FileNotFoundError:
        print(f"El archivo {ruta_archivo} no fue encontrado.")
        return []
    except Exception as e:
        print(f"Ocurrió un error al leer el archivo: {e}")
        return []

# Ejemplo de uso
mensajes = leer_archivo_txt(actions_route)
for mensaje in mensajes:
    print(mensaje)
