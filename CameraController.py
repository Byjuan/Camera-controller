from google import genai
from google.genai import types
import os
import queue
import json
import sounddevice as sd
from vosk import Model, KaldiRecognizer
from gtts import gTTS
from pygame import mixer
import tempfile
import time
import cv2 as cv
import numpy as np
import pygame
import sys

class ColorDetectorSystem:
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
        pygame.display.set_caption("Sistema de Detección de Colores por Voz")
        
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
        self.slider_values = self._get_current_slider_values()
        self.slider_rects = []
        
        # Cámara
        self.cap = cv.VideoCapture(0)
        self.clock = pygame.time.Clock()
        
        # Configuración de audio
        mixer.init()
        self.temp_files = []

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

        self.procesar_colores_tool = types.FunctionDeclaration(
            name='procesar_colores',
            description='Procesa los rangos de color desde un archivo.',
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    'color_name': types.Schema(
                        type=types.Type.STRING,
                        description='Nombre del color a procesar (Negro, Azul, Verde, Rojo, Morado)'
                    )
                },
                required=['color_name']
            )
        )

        self.tools = types.Tool(function_declarations=[self.detectar_color_tool, self.procesar_colores_tool])
        self.config = types.GenerateContentConfig(tools=[self.tools])

    def _get_current_slider_values(self):
        """Obtiene los valores actuales de los sliders"""
        current_color = self.colores[self.color_seleccionado]
        return self.rangos[current_color][0] + self.rangos[current_color][1]

    def detectar_color(self, color: str):
        """Función para detectar colores con la cámara"""
        print(f"Iniciando detector de color: {color}")
        
        if color in self.colores:
            self.color_seleccionado = self.colores.index(color)
            self.slider_values = self._get_current_slider_values()
        
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self._handle_mouse_click(pygame.mouse.get_pos())
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False

            # Procesamiento de frame
            ret, frame = self.cap.read()
            if not ret:
                continue

            frame_small = cv.resize(frame, (340, 260))
            mask = self._apply_color_mask(frame_small)

            # Renderizado
            self.screen.fill((240, 240, 240))
            self._draw_ui_elements(frame_small, mask)
            pygame.display.flip()
            self.clock.tick(30)
            
        print("Detector de colores cerrado")

    def _handle_mouse_click(self, mouse_pos):
        """Maneja los eventos de clic del mouse"""
        mx, my = mouse_pos
        
        # Sliders
        for i, rect in enumerate(self.slider_rects):
            if rect.collidepoint(mx, my):
                self._update_slider_value(i, mx)
                break
                
        # Selector de color
        color_rects = self._draw_color_selector()
        for idx, rect in enumerate(color_rects):
            if rect.collidepoint(mx, my):
                self.color_seleccionado = idx
                self.slider_values = self._get_current_slider_values()
                break
                
        # Botón de guardar
        if hasattr(self, 'save_color_rect') and self.save_color_rect.collidepoint(mx, my):
            self._save_color_range()

    def _update_slider_value(self, slider_idx, mouse_x):
        """Actualiza el valor de un slider basado en la posición del mouse"""
        rect = self.slider_rects[slider_idx]
        min_val, max_val = self.slider_ranges[slider_idx]
        rel_x = mouse_x - rect.x
        rel_x = max(0, min(rect.width, rel_x))
        value = int(min_val + (rel_x / rect.width) * (max_val - min_val))
        self.slider_values[slider_idx] = value
        
        # Actualizar rangos
        current_color = self.colores[self.color_seleccionado]
        if slider_idx < 3:
            self.rangos[current_color][0][slider_idx] = value
        else:
            self.rangos[current_color][1][slider_idx-3] = value

    def _apply_color_mask(self, frame):
        """Aplica la máscara de color al frame"""
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

    def _draw_ui_elements(self, frame, mask):
        """Dibuja todos los elementos de la interfaz de usuario"""
        # Sliders
        self.slider_rects = []
        for i, (label, (min_val, max_val), value) in enumerate(zip(self.slider_labels, self.slider_ranges, self.slider_values)):
            rect = self._draw_slider(60, 60 + i * 48, 380, 22, min_val, max_val, value, label)
            self.slider_rects.append(rect)

        # Selector de color
        self._draw_color_selector()

        # Botón de guardar
        self.save_color_rect = pygame.Rect(self.WIDTH - 200, self.HEIGHT - 60, 140, 40)
        pygame.draw.rect(self.screen, (220, 220, 220), self.save_color_rect, border_radius=8)
        txt_save = self.FONT.render("Guardar", True, (0, 0, 0))
        self.screen.blit(txt_save, (self.save_color_rect.x + 15, self.save_color_rect.y + 8))

        # Mostrar frame y máscara
        surf_frame = self._cvimg_to_pygame(frame)
        surf_mask = self._mask_to_pygame(mask)
        self.screen.blit(surf_frame, (500, 60))
        self.screen.blit(surf_mask, (850, 60))
        pygame.draw.rect(self.screen, (0, 0, 0), (500, 60, 340, 260), 2)
        pygame.draw.rect(self.screen, (0, 0, 0), (850, 60, 340, 260), 2)
        self.screen.blit(self.SMALL_FONT.render("Original", True, (0,0,0)), (500, 40))
        self.screen.blit(self.SMALL_FONT.render("Mask", True, (0,0,0)), (850, 40))

    def _draw_slider(self, x, y, w, h, min_val, max_val, value, label):
        """Dibuja un slider en la interfaz"""
        pygame.draw.rect(self.screen, (200, 200, 200), (x, y, w, h), border_radius=6)
        pos = int((value - min_val) / (max_val - min_val) * w)
        pygame.draw.rect(self.screen, (100, 100, 255), (x + pos - 7, y - 5, 14, h + 10), border_radius=7)
        txt = self.SMALL_FONT.render(f"{label}: {value}", True, (0, 0, 0))
        self.screen.blit(txt, (x + w + 15, y))
        return pygame.Rect(x, y, w, h)

    def _draw_color_selector(self):
        """Dibuja el selector de colores"""
        rects = []
        for idx, color in enumerate(self.colores):
            rect = pygame.Rect(60, 400 + idx * 48, 140, 40)
            pygame.draw.rect(self.screen, (180, 180, 255) if idx == self.color_seleccionado else (220, 220, 220), rect, border_radius=8)
            txt = self.FONT.render(color, True, (0, 0, 0))
            self.screen.blit(txt, (rect.x + 15, rect.y + 8))
            rects.append(rect)
        return rects

    def _save_color_range(self):
        """Guarda los rangos de color en un archivo"""
        color = self.colores[self.color_seleccionado]
        file_name = "color_ranges.txt"
        try:
            with open(file_name, "w") as f:
                f.write(f"Color: {color}\n")
                f.write(f"H low, S low, V low: {self.rangos[color][0]}\n")
                f.write(f"H high, S high, V high: {self.rangos[color][1]}\n")
            print(f"Rango HSV para {color} guardado en {file_name}")
        except Exception as e:
            print(f"Error al guardar el rango HSV: {e}")

    def procesar_colores(self, color_name: str):
        """
        Procesa los rangos de color desde el archivo guardado.
        
        Args:
            color_name (str): Nombre del color a procesar.
        """
        file_name = "color_ranges.txt"
        if not os.path.exists(file_name):
            print("No se encontró el archivo con rangos de color")
            return None
            
        with open(file_name, 'r') as f:
            lines = f.readlines()
            
        color_data = []
        current_color = None
        
        for line in lines:
            line = line.strip()
            if line.startswith("Color:"):
                current_color = line.split(":")[1].strip()
            elif current_color == color_name and ("low" in line or "high" in line):
                values = line.split(":")[1].strip()
                values = list(map(int, values.replace('[', '').replace(']', '').split(',')))
                color_data.append(values)
                
        if color_data:
            print(f"Rangos para {color_name}:")
            print(f"Bajo: {color_data[0]}")
            print(f"Alto: {color_data[1]}")
            return color_data
        else:
            print(f"No se encontraron datos para el color {color_name}")
            return None

    def _cvimg_to_pygame(self, img):
        """Convierte una imagen OpenCV a una superficie Pygame"""
        img = cv.cvtColor(img, cv.COLOR_BGR2RGB)
        img = np.rot90(img)
        return pygame.surfarray.make_surface(img)

    def _mask_to_pygame(self, mask):
        """Convierte una máscara a una superficie Pygame"""
        mask_rgb = cv.cvtColor(mask, cv.COLOR_GRAY2RGB)
        mask_rgb = np.rot90(mask_rgb)
        return pygame.surfarray.make_surface(mask_rgb)

    def escuchar(self, timeout=10):
        """Escucha comandos de voz usando Vosk"""
        try:
            model = Model(self.vosk_path) if self.vosk_path else Model(lang=self.vosk_model_lang)
            q = queue.Queue()
            
            def callback(indata, frames, time, status):
                q.put(bytes(indata))
            
            with sd.RawInputStream(samplerate=16000, blocksize=8000, 
                                dtype="int16", channels=1, callback=callback):
                print("Di tu comando...")
                
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

    def _text_to_speech(self, text):
        """Convierte texto a voz usando gTTS"""
        try:
            tts = gTTS(text=text, lang='es')
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as fp:
                temp_file = fp.name
                tts.save(temp_file)
            self.temp_files.append(temp_file)
            mixer.music.load(temp_file)
            mixer.music.play()
            while mixer.music.get_busy():
                pygame.time.Clock().tick(10)
        except Exception as e:
            print(f"Error en síntesis de voz: {e}")

    def ejecutar(self):
        """Bucle principal del sistema"""
        print("Sistema de detección de colores por voz iniciado")
        print("Di 'detectar color [nombre]' o 'procesar color [nombre]'")
        
        while True:
            comando = self.escuchar()
            
            if not comando:
                print("No se detectó comando, intenta nuevamente")
                continue
                
            if "salir" in comando.lower():
                print("Cerrando sistema...")
                self._cleanup()
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
                        self._text_to_speech(f"Iniciando detección de color {llamada_funcion.args['color']}")
                        self.detectar_color(**llamada_funcion.args)
                    elif llamada_funcion.name == "procesar_colores":
                        result = self.procesar_colores(**llamada_funcion.args)
                        if result:
                            self._text_to_speech(f"Rangos para {llamada_funcion.args['color_name']} procesados")
                        else:
                            self._text_to_speech("No se encontraron datos para ese color")
                    else:
                        self._text_to_speech("Comando no reconocido")
                
                else:
                    print(respuesta.text)
                    self._text_to_speech(respuesta.text)
                    
            except Exception as e:
                print("Error:", e)
                self._text_to_speech("Lo siento, hubo un error al procesar tu comando")

    def _cleanup(self):
        """Limpia recursos al cerrar el sistema"""
        self.cap.release()
        pygame.quit()
        for file in self.temp_files:
            try:
                os.remove(file)
            except:
                pass

if __name__ == "__main__":
    system = ColorDetectorSystem(debug=True)
    system.ejecutar()