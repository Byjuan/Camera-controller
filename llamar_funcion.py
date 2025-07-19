from google import genai
from google.genai import types
import os
import queue
import json
import sounddevice
from vosk import Model, KaldiRecognizer
from gtts import gTTS
from pygame import mixer
import tempfile
import time

class CalculoVoz:
    def __init__(self, vosk_path=None, vosk_model_lang="es", debug=False):
        # Configuración de voz
        self.vosk_path = vosk_path
        self.vosk_model_lang = vosk_model_lang
        self.debug = debug
        
        # Configuración de Gemini
        self.client = genai.Client(api_key="AIzaSyD--kHOT3Vp6QiuaXNyBA_Zx0L6CQ-lUls")
        self._setup_tools()
        
    def _setup_tools(self):
        """Configura las herramientas para Gemini"""
        self.sumar_tool = types.FunctionDeclaration(
            name='sumar_numeros',
            description='Suma dos números.',
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    'num1': types.Schema(type=types.Type.NUMBER, description='El primer número a sumar.'),
                    'num2': types.Schema(type=types.Type.NUMBER, description='El segundo número a sumar.'),
                },
                required=['num1', 'num2']
            )
        )

        self.restar_tool = types.FunctionDeclaration(
            name='restar_numeros',
            description='Resta dos números. Resta el segundo número del primero.',
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    'num1': types.Schema(type=types.Type.NUMBER, description='El número del que se restará (minuendo).'),
                    'num2': types.Schema(type=types.Type.NUMBER, description='El número a restar (sustraendo).'),
                },
                required=['num1', 'num2']
            )
        )

        self.multiplicar_tool = types.FunctionDeclaration(
            name='multiplicar_numeros',
            description='Multiplica dos números.',
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    'num1': types.Schema(type=types.Type.NUMBER, description='El primer número a multiplicar.'),
                    'num2': types.Schema(type=types.Type.NUMBER, description='El segundo número a multiplicar.'),
                },
                required=['num1', 'num2']
            )
        )

        self.dividir_tool = types.FunctionDeclaration( 
            name='dividir_numeros',
            description='Divide el primer número por el segundo. Maneja la división por cero.',
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    'num1': types.Schema(type=types.Type.NUMBER, description='El dividendo.'),
                    'num2': types.Schema(type=types.Type.NUMBER, description='El divisor.'),
                },
                required=['num1', 'num2']
            )
        )

        self.tools_list = [self.sumar_tool, self.restar_tool, self.multiplicar_tool, self.dividir_tool] 
        self.tools = types.Tool(function_declarations=self.tools_list)
        self.config = types.GenerateContentConfig(tools=[self.tools])

    # Métodos de cálculo (solo voz)
    def sumar_numeros(self, num1: float, num2: float):
        resultado = num1 + num2
        self.hablar(f"El resultado de la suma es {resultado}")

    def restar_numeros(self, num1: float, num2: float):
        resultado = num1 - num2
        self.hablar(f"El resultado de la resta es {resultado}")

    def multiplicar_numeros(self, num1: float, num2: float):
        resultado = num1 * num2
        self.hablar(f"El resultado de la multiplicación es {resultado}")

    def dividir_numeros(self, num1: float, num2: float):
        if num2 == 0:
            self.hablar("Error: No se puede dividir por cero")
        else:
            self.hablar(f"El resultado de la división es {num1 / num2}")

    # Método hablar corregido (con pygame)
    def hablar(self, texto: str):
        try:
            if self.debug:
                print(f"(Debug): {texto}")

            # Generar archivo de audio temporal con nombre único
            temp_file = os.path.join(tempfile.gettempdir(), f"voz_{time.time_ns()}.mp3")
            tts = gTTS(text=texto, lang=self.vosk_model_lang, slow=False)
            tts.save(temp_file)
            
            # Reproducir con pygame
            mixer.init()
            mixer.music.load(temp_file)
            mixer.music.play()
            
            # Esperar a que termine la reproducción
            while mixer.music.get_busy():
                time.sleep(0.05)
                
            # Limpieza
            mixer.quit()
            if os.path.exists(temp_file):
                os.remove(temp_file)
                
        except Exception as e:
            print(f"Error en voz: {e}")
            if 'temp_file' in locals() and os.path.exists(temp_file):
                os.remove(temp_file)

    # Método escuchar (sin cambios)
    def escuchar(self, timeout=10):
        try:
            model = Model(self.vosk_path) if self.vosk_path else Model(lang=self.vosk_model_lang)
            q = queue.Queue()
            
            def callback(indata, frames, time, status):
                q.put(bytes(indata))
            
            with sounddevice.RawInputStream(samplerate=16000, blocksize=8000, 
                                        dtype="int16", channels=1, callback=callback):
                self.hablar("Di tu operación matemática")
                
                recognizer = KaldiRecognizer(model, 16000)
                texto_final = ""
                silencio_contador = 0
                inicio_tiempo = time.time()
                
                while True:
                    if time.time() - inicio_tiempo > timeout:
                        self.hablar("Tiempo de espera agotado")
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
        self.hablar("Bienvenido a la calculadora por voz")
        
        while True:
            comando = self.escuchar()
            
            if not comando:
                self.hablar("No te he entendido, por favor repite")
                continue
                
            if "salir" in comando.lower():
                self.hablar("Hasta luego, adiós")
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
                    
                    if llamada_funcion.name == "sumar_numeros":
                        self.sumar_numeros(**llamada_funcion.args)
                    elif llamada_funcion.name == "restar_numeros":
                        self.restar_numeros(**llamada_funcion.args)
                    elif llamada_funcion.name == "multiplicar_numeros":
                        self.multiplicar_numeros(**llamada_funcion.args)
                    elif llamada_funcion.name == "dividir_numeros":
                        self.dividir_numeros(**llamada_funcion.args)
                    else:
                        self.hablar("Operación no reconocida")
                
                else:
                    self.hablar(respuesta.text)
                    
            except Exception as e:
                self.hablar("Lo siento, hubo un error")

if __name__ == "__main__":
    # Ejecutar en modo producción (solo voz)
    calculadora = CalculoVoz(debug=False)  # Cambia a True para ver mensajes de depuración
    calculadora.ejecutar()