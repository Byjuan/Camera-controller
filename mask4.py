import pygame
import cv2
import numpy as np
from pygame.locals import *

# Inicialización de Pygame
pygame.init()
WIDTH, HEIGHT = 1200, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("LAB Color Mask Configurator")

# Inicialización de OpenCV
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: No se pudo abrir la cámara")
    exit()

# Colores predeterminados (LAB) - valores ajustados
predefined_colors = [
    {"name": "Rojo", "low": (0, 150, 100), "high": (100, 255, 255)},
    {"name": "Verde", "low": (0, 0, 0), "high": (100, 120, 150)},
    {"name": "Azul", "low": (0, 150, 0), "high": (100, 255, 120)},
    {"name": "Amarillo", "low": (0, 0, 150), "high": (100, 120, 255)},
    {"name": "Naranja", "low": (0, 120, 150), "high": (100, 200, 255)},
    {"name": "Morado", "low": (0, 150, 120), "high": (100, 200, 200)},
    {"name": "Rosa", "low": (0, 100, 150), "high": (100, 180, 255)},
    {"name": "Blanco", "low": (200, 128, 128), "high": (255, 128, 128)},
    {"name": "Negro", "low": (0, 128, 128), "high": (50, 128, 128)},
    {"name": "Gris", "low": (100, 128, 128), "high": (200, 128, 128)}
]

# Función para convertir LAB a RGB (para visualización)
def lab_to_rgb(l, a, b):
    lab_pixel = np.uint8([[[l, a, b]]])
    bgr_pixel = cv2.cvtColor(lab_pixel, cv2.COLOR_LAB2BGR)
    rgb_pixel = cv2.cvtColor(bgr_pixel, cv2.COLOR_BGR2RGB)
    return tuple(int(c) for c in rgb_pixel[0][0])

# Definir funciones antes de usarlas
def apply_color(data):
    low = data["low"]
    high = data["high"]
    
    sliders[0].val = low[0]  # Low L
    sliders[1].val = high[0] # High L
    sliders[2].val = low[1]  # Low A
    sliders[3].val = high[1] # High A
    sliders[4].val = low[2]  # Low B
    sliders[5].val = high[2] # High B
    
    # Actualizar posiciones de los knobs
    for i, slider in enumerate(sliders):
        rel_x = (slider.val - slider.min_val) / (slider.max_val - slider.min_val) * slider.rect.width
        slider.knob_x = slider.rect.x + rel_x

def save_colors_to_file():
    with open("saved_colors.txt", "w") as file:
        for color in saved_colors:
            file.write(f"Color {color['name']}:\n")
            file.write(f"Low: {list(color['low'])}\n")
            file.write(f"High: {list(color['high'])}\n\n")

def load_colors_from_file():
    try:
        with open("saved_colors.txt", "r") as file:
            lines = file.readlines()
            i = 0
            while i < len(lines):
                if lines[i].startswith("Color "):
                    name = lines[i].split(":")[0].replace("Color ", "").strip()
                    low = eval(lines[i+1].split(":")[1].strip())
                    high = eval(lines[i+2].split(":")[1].strip())
                    
                    new_color = {
                        "name": name,
                        "low": tuple(low),
                        "high": tuple(high)
                    }
                    
                    saved_colors.append(new_color)
                    
                    # Crear botón para el color cargado
                    row = len(saved_colors) - 1
                    x = 400 + button_width + spacing
                    y = 50 + row * (button_height + spacing)
                    rgb_color = lab_to_rgb(low[0], low[1], low[2])
                    
                    new_button = Button(x, y, button_width, button_height, 
                                      rgb_color, name, 
                                      callback=apply_color, data=new_color)
                    saved_color_buttons.append(new_button)
                    
                    i += 4  # Saltar 4 líneas (nombre, low, high y línea en blanco)
                else:
                    i += 1
    except FileNotFoundError:
        pass  # No hay archivo guardado, empezamos con lista vacía

class Slider:
    def __init__(self, x, y, w, h, min_val, max_val, initial, label):
        self.rect = pygame.Rect(x, y, w, h)
        self.min_val = min_val
        self.max_val = max_val
        self.val = initial
        self.dragging = False
        self.label = label
        self.knob_radius = 10
        self.knob_x = x + (initial - min_val) / (max_val - min_val) * w
        
    def draw(self, surface):
        # Barra del slider
        pygame.draw.rect(surface, (100, 100, 100), self.rect, border_radius=5)
        pygame.draw.rect(surface, (200, 200, 200), self.rect, 2, border_radius=5)
        
        # Knob
        pygame.draw.circle(surface, (50, 150, 200), (int(self.knob_x), self.rect.centery), self.knob_radius)
        pygame.draw.circle(surface, (255, 255, 255), (int(self.knob_x), self.rect.centery), self.knob_radius, 2)
        
        # Texto
        font = pygame.font.SysFont(None, 28)
        text = font.render(f"{self.label}: {int(self.val)}", True, (255, 255, 255))
        surface.blit(text, (self.rect.x, self.rect.y - 25))
        
    def handle_event(self, event):
        if event.type == MOUSEBUTTONDOWN:
            if event.button == 1:
                knob_rect = pygame.Rect(self.knob_x - self.knob_radius, 
                                       self.rect.centery - self.knob_radius,
                                       self.knob_radius * 2, 
                                       self.knob_radius * 2)
                if knob_rect.collidepoint(event.pos):
                    self.dragging = True
                    
        elif event.type == MOUSEBUTTONUP:
            if event.button == 1:
                self.dragging = False
                
        elif event.type == MOUSEMOTION and self.dragging:
            rel_x = event.pos[0] - self.rect.x
            rel_x = max(0, min(rel_x, self.rect.width))
            self.val = self.min_val + (rel_x / self.rect.width) * (self.max_val - self.min_val)
            self.knob_x = self.rect.x + rel_x

class Button:
    def __init__(self, x, y, w, h, color, text, callback=None, data=None):
        self.rect = pygame.Rect(x, y, w, h)
        self.color = color
        self.text = text
        self.callback = callback
        self.data = data
        
    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect, border_radius=5)
        pygame.draw.rect(surface, (200, 200, 200), self.rect, 2, border_radius=5)
        
        font = pygame.font.SysFont(None, 24)
        text_surf = font.render(self.text, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)
        
    def handle_event(self, event):
        if event.type == MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                if self.callback:
                    if self.data is not None:
                        self.callback(self.data)
                    else:
                        self.callback()
                return True
        return False

# Crear sliders
sliders = [
    Slider(50, 50, 300, 20, 0, 255, 0, "Low L"),
    Slider(50, 100, 300, 20, 0, 255, 255, "High L"),
    Slider(50, 150, 300, 20, 0, 255, 0, "Low A"),
    Slider(50, 200, 300, 20, 0, 255, 255, "High A"),
    Slider(50, 250, 300, 20, 0, 255, 0, "Low B"),
    Slider(50, 300, 300, 20, 0, 255, 255, "High B")
]

# Crear botones para colores predefinidos
color_buttons = []
button_width, button_height = 100, 30
spacing = 10

for i, color_data in enumerate(predefined_colors):
    x = 400
    y = 50 + i * (button_height + spacing)
    
    # Crear color de fondo aproximado
    rgb_color = lab_to_rgb(*color_data["low"])
    
    button = Button(x, y, button_width, button_height, 
                   rgb_color, color_data["name"], 
                   callback=apply_color, data=color_data)
    color_buttons.append(button)

# Botón para guardar
save_button = Button(50, 350, 150, 40, (0, 100, 0), "Guardar Color")

# Lista para colores guardados
saved_colors = []
saved_color_buttons = []

# Cargar colores guardados al iniciar
load_colors_from_file()

def save_current_color():
    low_l = int(sliders[0].val)
    high_l = int(sliders[1].val)
    low_a = int(sliders[2].val)
    high_a = int(sliders[3].val)
    low_b = int(sliders[4].val)
    high_b = int(sliders[5].val)
    
    color_name = f"Color {len(saved_colors) + 1}"
    new_color = {
        "name": color_name,
        "low": (low_l, low_a, low_b),
        "high": (high_l, high_a, high_b)
    }
    
    saved_colors.append(new_color)
    
    # Crear nuevo botón en posición separada
    row = len(saved_colors) - 1
    x = 400 + button_width + spacing  # Columna derecha
    y = 50 + row * (button_height + spacing)
    
    # Crear color de fondo aproximado
    rgb_color = lab_to_rgb(low_l, low_a, low_b)
    
    new_button = Button(x, y, button_width, button_height, 
                       rgb_color, color_name, 
                       callback=apply_color, data=new_color)
    saved_color_buttons.append(new_button)
    
    # Guardar inmediatamente al crear el color
    save_colors_to_file()

# Áreas de visualización
camera_rect = pygame.Rect(600, 50, 320, 240)
mask_rect = pygame.Rect(950, 50, 320, 240)
color_mask_rect = pygame.Rect(600, 320, 320, 240)

# Rectángulos de color
low_color_rect = pygame.Rect(220, 350, 50, 40)
high_color_rect = pygame.Rect(280, 350, 50, 40)

# Main loop
running = True
clock = pygame.time.Clock()

while running:
    for event in pygame.event.get():
        if event.type == QUIT:
            running = False
        
        # Manejar eventos de sliders
        for slider in sliders:
            slider.handle_event(event)
        
        # Manejar eventos de botones
        for button in color_buttons:
            if button.handle_event(event):
                apply_color(button.data)
                
        for button in saved_color_buttons:
            if button.handle_event(event):
                apply_color(button.data)
                
        if save_button.handle_event(event):
            save_current_color()
    
    # Obtener valores actuales de los sliders
    low_l = int(sliders[0].val)
    high_l = int(sliders[1].val)
    low_a = int(sliders[2].val)
    high_a = int(sliders[3].val)
    low_b = int(sliders[4].val)
    high_b = int(sliders[5].val)
    
    # Capturar frame de la cámara
    ret, frame = cap.read()
    if not ret:
        continue
    
    # Procesamiento de OpenCV
    frame = cv2.resize(frame, (320, 240))
    lab_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
    
    # Crear máscara
    lower_bound = np.array([low_l, low_a, low_b])
    upper_bound = np.array([high_l, high_a, high_b])
    mask = cv2.inRange(lab_frame, lower_bound, upper_bound)
    
    # Aplicar máscara
    color_mask = cv2.bitwise_and(frame, frame, mask=mask)
    
    # Convertir imágenes para Pygame con conversión correcta de color
    # Cámara: BGR a RGB
    camera_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    camera_surf = pygame.surfarray.make_surface(camera_rgb.swapaxes(0, 1))
    
    # Máscara binaria (ya es monocromática)
    mask_rgb = cv2.cvtColor(mask, cv2.COLOR_GRAY2RGB)
    mask_surf = pygame.surfarray.make_surface(mask_rgb.swapaxes(0, 1))
    
    # Máscara de color: BGR a RGB
    color_mask_rgb = cv2.cvtColor(color_mask, cv2.COLOR_BGR2RGB)
    color_mask_surf = pygame.surfarray.make_surface(color_mask_rgb.swapaxes(0, 1))
    
    # Dibujar interfaz
    screen.fill((30, 30, 50))
    
    # Dibujar sliders
    for slider in sliders:
        slider.draw(screen)
    
    # Dibujar botones predeterminados
    for button in color_buttons:
        button.draw(screen)
    
    # Dibujar botones guardados
    for button in saved_color_buttons:
        button.draw(screen)
    
    # Dibujar botón guardar
    save_button.draw(screen)
    
    # Dibujar áreas de visualización
    pygame.draw.rect(screen, (100, 100, 100), camera_rect, border_radius=5)
    pygame.draw.rect(screen, (100, 100, 100), mask_rect, border_radius=5)
    pygame.draw.rect(screen, (100, 100, 100), color_mask_rect, border_radius=5)
    
    # Dibujar imágenes
    if camera_surf:
        screen.blit(camera_surf, camera_rect)
    if mask_surf:
        screen.blit(mask_surf, mask_rect)
    if color_mask_surf:
        screen.blit(color_mask_surf, color_mask_rect)
    
    # Dibujar etiquetas
    font = pygame.font.SysFont(None, 32)
    screen.blit(font.render("Cámara", True, (255, 255, 255)), (camera_rect.x, camera_rect.y - 30))
    screen.blit(font.render("Máscara Binaria", True, (255, 255, 255)), (mask_rect.x, mask_rect.y - 30))
    screen.blit(font.render("Máscara de Color", True, (255, 255, 255)), (color_mask_rect.x, color_mask_rect.y - 30))
    
    # Dibujar cuadros de color
    pygame.draw.rect(screen, lab_to_rgb(low_l, low_a, low_b), low_color_rect)
    pygame.draw.rect(screen, (200, 200, 200), low_color_rect, 2)
    pygame.draw.rect(screen, lab_to_rgb(high_l, high_a, high_b), high_color_rect)
    pygame.draw.rect(screen, (200, 200, 200), high_color_rect, 2)
    
    # Dibujar etiquetas de colores
    font = pygame.font.SysFont(None, 24)
    screen.blit(font.render("Bajo", True, (255, 255, 255)), (low_color_rect.x, low_color_rect.y - 25))
    screen.blit(font.render("Alto", True, (255, 255, 255)), (high_color_rect.x, high_color_rect.y - 25))
    
    pygame.display.flip()
    clock.tick(30)

# Guardar colores al cerrar la aplicación (por si acaso)
save_colors_to_file()

# Liberar recursos
cap.release()
pygame.quit()