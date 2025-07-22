import cv2
import numpy as np

# Diccionario de rangos de colores en HSV
color_ranges = {
    "rojo": ([0, 100, 100], [10, 255, 255], [160, 100, 100], [180, 255, 255]),
    "verde": ([40, 50, 50], [80, 255, 255]),
    "amarillo": ([20, 100, 100], [40, 255, 255]),
    "azul": ([90, 50, 50], [130, 255, 255]),
    "morado": ([130, 50, 50], [160, 255, 255]),
    "blanco": ([0, 0, 200], [180, 30, 255]),
    "negro": ([0, 0, 0], [180, 255, 30]),
    "rosado": ([140, 50, 50], [170, 255, 255])
}

# Inicializar la cámara
cap = cv2.VideoCapture(0)

# Variable para guardar el color seleccionado
current_color = None

while True:
    ret, frame = cap.read()
    if not ret:
        break

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    
    # Mostrar instrucciones
    cv2.putText(frame, "Presiona: r, g, y, b, p, k, w, m (ESC para salir)", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    # Esperar la tecla del usuario
    key = cv2.waitKey(1) & 0xFF
    if key == 27:  # ESC para salir
        break

    # Actualizar el color seleccionado según la tecla
    if key == ord('r'):
        current_color = "rojo"
    elif key == ord('g'):
        current_color = "verde"
    elif key == ord('y'):
        current_color = "amarillo"
    elif key == ord('b'):
        current_color = "azul"
    elif key == ord('p'):
        current_color = "morado"
    elif key == ord('k'):
        current_color = "negro"
    elif key == ord('w'):
        current_color = "blanco"
    elif key == ord('m'):
        current_color = "rosado"

    # Mostrar máscara y resultado SI hay un color seleccionado
    if current_color:
        if current_color == "rojo":
            # Rojo necesita dos rangos
            lower1 = np.array(color_ranges["rojo"][0])
            upper1 = np.array(color_ranges["rojo"][1])
            lower2 = np.array(color_ranges["rojo"][2])
            upper2 = np.array(color_ranges["rojo"][3])
            mask1 = cv2.inRange(hsv, lower1, upper1)
            mask2 = cv2.inRange(hsv, lower2, upper2)
            mask = cv2.bitwise_or(mask1, mask2)
        else:
            lower = np.array(color_ranges[current_color][0])
            upper = np.array(color_ranges[current_color][1])
            mask = cv2.inRange(hsv, lower, upper)

        res = cv2.bitwise_and(frame, frame, mask=mask)

        # Mostrar las ventanas de máscara y resultado
        cv2.imshow("Original", frame)
        cv2.imshow(f"Mascara {current_color}", mask)
        cv2.imshow(f"Resultado {current_color}", res)
    else:
        cv2.imshow("Original", frame)

    # Cerrar ventanas de máscaras anteriores si no hay color seleccionado
    if not current_color:
        for win in ["Mascara", "Resultado"]:
            if cv2.getWindowProperty(win, cv2.WND_PROP_VISIBLE) >= 1:
                cv2.destroyWindow(win)

# Liberar recursos
cap.release()
cv2.destroyAllWindows()