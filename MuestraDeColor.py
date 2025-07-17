import cv2
import numpy as np

# Dictionary of LAB ranges for each color to detect.
# Each color has a lower and upper bound in the LAB color space.
# Red has two ranges because it appears at both ends of the LAB color space.
COLOR_RANGES_LAB = {
    "negro": {
        "lower": np.array([0, 0, 0]),
        "upper": np.array([50, 255, 255])
    },
    "azul": {
        "lower": np.array([20, 150, 130]),
        "upper": np.array([100, 200, 180])
    },
    "verde": {
        "lower": np.array([40, 110, 110]),
        "upper": np.array([200, 140, 140])
    },
    "rojo": {
        "lower1": np.array([20, 150, 150]),
        "upper1": np.array([80, 200, 200]),
        "lower2": np.array([170, 140, 140]),
        "upper2": np.array([255, 200, 200])
    },
    "morado": {
        "lower": np.array([40, 170, 120]),
        "upper": np.array([180, 210, 180])
    },
    "amarillo": {
        "lower": np.array([180, 120, 120]),
        "upper": np.array([255, 150, 170])
    }
}

def mostrar_menu_colores():
    """
    Prints a menu in the terminal with the available colors to detect.
    """
    print("Type the names of one or more colors to detect, separated by commas (example: azul,rojo,verde):")
    for color in COLOR_RANGES_LAB.keys():
        print(f"- {color}")

def seleccionar_colores():
    """
    Allows the user to select one or more colors by name from the terminal.
    Returns a list with the names of the selected colors.
    """
    colores = list(COLOR_RANGES_LAB.keys())
    while True:
        mostrar_menu_colores()
        opciones = input("Enter the color names separated by commas: ")
        seleccionados = [c.strip().lower() for c in opciones.split(",")]
        if all(c in colores for c in seleccionados):
            return seleccionados
        else:
            print("Invalid color(s). Please enter valid color names from the list.")

def main():
    """
    Main function of the program.
    Allows the user to select colors from the terminal and then starts object detection for those colors using the camera.
    """
    colores_seleccionados = seleccionar_colores()
    print(f"Detecting objects of color: {', '.join([c.upper() for c in colores_seleccionados])}")

    # Initialize the camera
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Could not open the camera.")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Flip the image horizontally for a mirror effect
        frame = cv2.flip(frame, 1)
        # Convert the image from BGR to LAB
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2Lab)
        # Total mask for all selected colors
        mascara_total = np.zeros(lab.shape[:2], dtype=np.uint8)
        contadores = {}

        # Process each selected color
        for color in colores_seleccionados:
            rango = COLOR_RANGES_LAB[color]
            if color == "rojo":
                # Red has two ranges in LAB
                mask1 = cv2.inRange(lab, rango["lower1"], rango["upper1"])
                mask2 = cv2.inRange(lab, rango["lower2"], rango["upper2"])
                mask = cv2.bitwise_or(mask1, mask2)
            else:
                mask = cv2.inRange(lab, rango["lower"], rango["upper"])
            # Apply morphological operations to clean the mask
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((5,5),np.uint8))
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((5,5),np.uint8))
            mascara_total = cv2.bitwise_or(mascara_total, mask)

            # Find contours of the detected objects
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            objeto_count = 0
            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area > 1000:
                    x, y, w, h = cv2.boundingRect(cnt)
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0,255,255), 2)
                    objeto_count += 1
            contadores[color] = objeto_count

        # Show the count of detected objects per color on the image
        y_offset = 30
        for color in colores_seleccionados:
            cv2.putText(frame, f"{color.capitalize()}: {contadores[color]}", (10, y_offset),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255), 2)
            y_offset += 30

        # Show the camera image and the mask
        cv2.imshow("Camara", frame)
        cv2.imshow("Mascara", mascara_total)

        # Exit if the 'q' key is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()