from google import genai
from google.genia import types
import os
import queue
import json
import sounddevice
from vosk import Model, KaldiRecognizer
from gtts import gTTS
from pygame import mixer
import tempfile
import time
import cv2 as cv
import numpy as np
import pygame
import sys

class Camera_controller:
    def __init__(self, vosk_path=None, vosk_model_lang="es", debug=False):
        # Configuración de voz
        self.vosk_path = vosk_path
        self.vosk_model_lang = vosk_model_lang
        self.debug = debug
        
        # Configuración de Gemini
        self.client = genai.Client(api_key="AIzaSyD--kHOT3Vp6QiuaXNyBA_Zx0L6CQ-lUls")
        self._setup_tools()
        
        # Configuración del detector de colores
        pygame.init()
        self.WIDTH, self.HEIGHT = 1200, 650
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("Color Detector")
        
        self.FONT = pygame.font.SysFont("Arial", 20)
        self.SMALL_FONT = pygame.font.SysFont("Arial", 16)
        
        # Rangos HSV iniciales para cada color
        self.rangos = {
            "Negro": [[0, 0, 0], [179, 255, 60]],
            "Azul": [[90, 80, 40], [130, 255, 255]],
            "Verde": [[35, 80, 40], [85, 255, 255]],
            "Rojo": [[0, 100, 40], [10, 255, 255]],
            "Morado": [[130, 80, 40], [160, 255, 255]],
        }
        self.colores = list(self.rangos.keys())
        self.color_seleccionado = 1  # Azul por defecto
        
        # Sliders
        self.slider_labels = ["H low", "H high", "S low", "S high", "V low", "V high"]
        self.slider_ranges = [(0, 179), (0, 179), (0, 255), (0, 255), (0, 255), (0, 255)]
        self.slider_values = self.rangos[self.colores[self.color_seleccionado]][0] + self.rangos[self.colores[self.color_seleccionado]][1]
        self.slider_rects = []
        
        # Cámara
        self.cap = cv.VideoCapture(0)
        self.clock = pygame.time.Clock()
        
    def _setup_tools(self):
        """Configura las herramientas para Gemini"""
        self.detectar_color_tool = types.FunctionDeclaration(
            name='detectar_color',
            description='Inicia el detector de colores por cámara.',
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    'color': types.Schema(
                        type=types.Type.STRING, 
                        description='Color a detectar (Negro, Azul, Verde, Rojo, Morado)',
                        enum=["Negro", "Azul", "Verde", "Rojo", "Morado"]
                    ),
                },
                required=['color']
            )
        )

        self.tools_list = [self.detectar_color_tool]
        self.tools = types.Tool(function_declarations=self.tools_list)
        self.config = types.GenerateContentConfig(tools=[self.tools])

    def detectar_color(self, color: str):
        """Función para detectar colores con la cámara"""
        print(f"Iniciando detector de color: {color}")
        
        # Configurar el color seleccionado
        if color in self.colores:
            self.color_seleccionado = self.colores.index(color)
            self.update_sliders_from_color()
        
        # Bucle principal del detector de colores
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = pygame.mouse.get_pos()
                    # Sliders
                    self.update_slider_from_mouse(mx, my)
                    # Selector de color
                    color_rects = self.draw_color_selector()
                    for idx, rect in enumerate(color_rects):
                        if rect.collidepoint(mx, my):
                            self.color_seleccionado = idx
                            self.update_sliders_from_color()
                    # Botón de guardar
                    if self.save_color_rect.collidepoint(mx, my):
                        self.save_color_range()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False

            # Capturar frame de la cámara
            ret, frame = self.cap.read()
            if not ret:
                continue

            frame_small = cv.resize(frame, (340, 260))
            mask = self.opencv_mask_frame(frame_small)

            self.screen.fill((240, 240, 240))

            # Dibujar sliders
            self.slider_rects = []
            for i, (label, (min_val, max_val), value) in enumerate(zip(self.slider_labels, self.slider_ranges, self.slider_values)):
                rect = self.draw_slider(60, 60 + i * 48, 380, 22, min_val, max_val, value, label)
                self.slider_rects.append(rect)

            # Selector de color
            self.draw_color_selector()

            # Botón de guardar
            self.save_color_rect = pygame.Rect(self.WIDTH - 200, self.HEIGHT - 60, 140, 40)
            pygame.draw.rect(self.screen, (220, 220, 220), self.save_color_rect, border_radius=8)
            txt_save = self.FONT.render("Guardar", True, (0, 0, 0))
            self.screen.blit(txt_save, (self.save_color_rect.x + 15, self.save_color_rect.y + 8))

            # Mostrar frame original y máscara
            surf_frame = self.cvimg_to_pygame(frame_small)
            surf_mask = self.mask_to_pygame(mask)
            self.screen.blit(surf_frame, (500, 60))
            self.screen.blit(surf_mask, (850, 60))
            pygame.draw.rect(self.screen, (0, 0, 0), (500, 60, 340, 260), 2)
            pygame.draw.rect(self.screen, (0, 0, 0), (850, 60, 340, 260), 2)
            self.screen.blit(self.SMALL_FONT.render("Original", True, (0,0,0)), (500, 40))
            self.screen.blit(self.SMALL_FONT.render("Mask", True, (0,0,0)), (850, 40))

            pygame.display.flip()
            self.clock.tick(30)
            
        print("Detector de colores cerrado")

    # Métodos auxiliares para el detector de colores
    def draw_slider(self, x, y, w, h, min_val, max_val, value, label):
        """Dibuja un slider horizontal en la pantalla de pygame"""
        pygame.draw.rect(self.screen, (200, 200, 200), (x, y, w, h), border_radius=6)
        pos = int((value - min_val) / (max_val - min_val) * w)
        pygame.draw.rect(self.screen, (100, 100, 255), (x + pos - 7, y - 5, 14, h + 10), border_radius=7)
        txt = self.SMALL_FONT.render(f"{label}: {value}", True, (0, 0, 0))
        self.screen.blit(txt, (x + w + 15, y))
        return pygame.Rect(x, y, w, h)

    def update_slider_from_mouse(self, mx, my):
        """Actualiza el valor del slider cuando el usuario hace clic"""
        for i, rect in enumerate(self.slider_rects):
            if rect.collidepoint(mx, my):
                x, y, w, h = rect
                min_val, max_val = self.slider_ranges[i]
                rel_x = mx - x
                rel_x = max(0, min(w, rel_x))
                value = int(min_val + (rel_x / w) * (max_val - min_val))
                self.slider_values[i] = value
                self.rangos[self.colores[self.color_seleccionado]] = [
                    self.slider_values[:3], self.slider_values[3:]
                ]
                break

    def draw_color_selector(self):
        """Dibuja los botones de selección de color"""
        rects = []
        for idx, color in enumerate(self.colores):
            rect = pygame.Rect(60, 400 + idx * 48, 140, 40)
            pygame.draw.rect(self.screen, (180, 180, 255) if idx == self.color_seleccionado else (220, 220, 220), rect, border_radius=8)
            txt = self.FONT.render(color, True, (0, 0, 0))
            self.screen.blit(txt, (rect.x + 15, rect.y + 8))
            rects.append(rect)
        return rects

    def opencv_mask_frame(self, frame):
        """Aplica el rango HSV seleccionado y devuelve la máscara binaria"""
        hsv = cv.cvtColor(frame, cv.COLOR_BGR2HSV)
        color = self.colores[self.color_seleccionado]
        bajo, alto = self.rangos[color]
        bajo_np = np.array(bajo, dtype=np.uint8)
        alto_np = np.array(alto, dtype=np.uint8)

        if color == "Rojo":
            lower1 = np.array([0, bajo[1], bajo[2]], dtype=np.uint8)
            upper1 = np.array([alto[0], alto[1], alto[2]], dtype=np.uint8)
            mask1 = cv.inRange(hsv, lower1, upper1)
            lower2 = np.array([170, bajo[1], bajo[2]], dtype=np.uint8)
            upper2 = np.array([179, alto[1], alto[2]], dtype=np.uint8)
            mask2 = cv.inRange(hsv, lower2, upper2)
            mask = cv.bitwise_or(mask1, mask2)
        else:
            mask = cv.inRange(hsv, bajo_np, alto_np)

        kernel = np.ones((5, 5), np.uint8)
        mask = cv.erode(mask, kernel, iterations=1)
        mask = cv.dilate(mask, kernel, iterations=1)
        return mask

    def cvimg_to_pygame(self, img):
        """Convierte una imagen OpenCV BGR a una superficie Pygame"""
        img = cv.cvtColor(img, cv.COLOR_BGR2RGB)
        img = np.rot90(img)
        return pygame.surfarray.make_surface(img)

    def mask_to_pygame(self, mask):
        """Convierte una máscara binaria a una superficie Pygame"""
        mask_rgb = cv.cvtColor(mask, cv.COLOR_GRAY2RGB)
        mask_rgb = np.rot90(mask_rgb)
        return pygame.surfarray.make_surface(mask_rgb)

    def update_sliders_from_color(self):
        """Actualiza los valores de los sliders cuando se selecciona un nuevo color"""
        self.slider_values = self.rangos[self.colores[self.color_seleccionado]][0] + self.rangos[self.colores[self.color_seleccionado]][1]

    def save_color_range(self):
        """Guarda el rango HSV del color seleccionado en un archivo"""
        color = self.colores[self.color_seleccionado]
        file_name = "file.txt"
        try:
            with open(file_name, "w") as f:
                f.write(f"Color: {color}\n")
                f.write(f"H low, S low, V low: {self.rangos[color][0]}\n")
                f.write(f"H high, S high, V high: {self.rangos[color][1]}\n")
            print(f"Rango HSV para {color} guardado en {file_name}")
        except Exception as e:
            print(f"Error al guardar el rango HSV: {e}")

    # Métodos de reconocimiento de voz (sin cambios)
    def escuchar(self, timeout=10):
        try:
            model = Model(self.vosk_path) if self.vosk_path else Model(lang=self.vosk_model_lang)
            q = queue.Queue()
            
            def callback(indata, frames, time, status):
                q.put(bytes(indata))
            
            with sounddevice.RawInputStream(samplerate=16000, blocksize=8000, 
                                        dtype="int16", channels=1, callback=callback):
                print("Di tu comando")
                
                recognizer = KaldiRecognizer(model, 16000)
                texto_final = ""
                silencio_contador = 0
                inicio_tiempo = time.time()
                
                while True:
                    if time.time() - inicio_tiempo > timeout:
                        print("Tiempo de espera agotado")
                        return ""
                    
                    data = q.get()
                    
                    if recognizer.AcceptWaveform(data):
                        resultado = json.loads(recognizer.Result())['text']
                        if resultado:
                            texto_final = resultado
                            break
                    else:
                        parcial = json.loads(recognizer.PartialResult())['partial']
                        if not parcial:
                            silencio_contador += 1
                        else:
                            silencio_contador = 0
                            
                    if silencio_contador >= 5:
                        break
                
                return texto_final.strip()
                
        except Exception as e:
            print(f"Error en reconocimiento: {e}")
            return ""

    def ejecutar(self):
        print("Bienvenido al sistema de voz")
        
        while True:
            comando = self.escuchar()
            
            if not comando:
                print("No te he entendido, por favor repite")
                continue
                
            if "salir" in comando.lower():
                print("Hasta luego, adiós")
                self.cap.release()
                pygame.quit()
                break

            try:
                respuesta = self.client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=comando,
                    config=self.config,
                )
                
                if (respuesta.candidates and 
                    respuesta.candidates[0].content.parts and 
                    respuesta.candidates[0].content.parts[0].function_call):
                    
                    llamada_funcion = respuesta.candidates[0].content.parts[0].function_call
                    
                    if llamada_funcion.name == "detectar_color":
                        self.detectar_color(**llamada_funcion.args)
                    else:
                        print("no se reconocio tu orden")
                
                else:
                    print(respuesta.text)
                    
            except Exception as e:
                print("Lo siento, hubo un error:", e)

if __name__ == "__main__":
    camera_controller = Camera_controller(debug=False)
    camera_controller.ejecutar()