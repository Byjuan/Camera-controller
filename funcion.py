import os

def procesar_colores(nombre_archivo='file.txt',color_name=''):
    """
    Lee un archivo, extrae rangos de color HSV y los imprime.

    Args:
        nombre_archivo (str): El nombre del archivo a leer.
    
    Returns:
        list: Una lista de los valores 'low' y 'high' de los colores.
    """
    color_finaly = []
    with open(nombre_archivo, 'r') as f:
        file = f.readlines()
        for line in file:
            color_bajo = []
            color_alto = []
            if "low" in line and color_name in file[file.index(line) -1 ]:
                color_bajo = line.split(':')[1].strip()
                low = list(map(int, color_bajo.replace('[', '').replace(']', '').split(',')))  
                print(f"Color {color_name} bajo: {low}")
            elif "high" in line and color_name in file[file.index(line) -2 ]:
                color_alto= line.split(':')[1].strip()
                high = list(map(int, color_alto.replace('[', '').replace(']', '').split(',')))    
                print(f"Color {color_name} alto: {high}")

            if color_bajo:
                color_finaly.append(low)
            elif color_alto:
                color_finaly.append(high)

    print(f"Color final {color_name}: {color_finaly}")
    return color_finaly

# Ejemplo de uso:
if __name__ == "__main__":
    resultados = procesar_colores(color_name='Azul')