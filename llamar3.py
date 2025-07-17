from google import genai
from google.genai import types
import json
from vosk import Model, KaldiRecognizer
import sounddevice as sd
import queue
import random

# --- Configuración de Gemini ---
suma_function = {
    "name": "sumar",
    "description": "Suma dos números",
    "parameters": {
        "type": "object",
        "properties": {
            "numero1": {"type": "number"},
            "numero2": {"type": "number"}
        },
        "required": ["numero1", "numero2"]
    }
}

client = genai.Client(api_key="AIzaSyAKIXenE4WIyx96A9T6WgLCD1feLk-DOYY")
tools = types.Tool(function_declarations=[suma_function])
config = types.GenerateContentConfig(tools=[tools])

# --- Función para sumar ---
def sumar(numero1=None, numero2=None):
    numero1 = numero1 if numero1 is not None else random.numero1
    numero2 = numero2 if numero2 is not None else random.numero2
    resultado = numero1 + numero2
    print(f"Suma: {numero1} + {numero2} = {resultado}")
    return resultado

# --- Configuración de Vosk para reconocimiento de voz ---
model = Model("modelos/vosk-model-es-0.42")  # Asegúrate de que la ruta del modelo es correcta
recognizer = KaldiRecognizer(model, 16000)

# Configuración del audio con sounddevice
sample_rate = 16000
block_size = 8192
audio_queue = queue.Queue()

def audio_callback(indata, frames, time, status):
    """Callback para capturar audio en tiempo real."""
    if status:
        print(f"Error en audio: {status}")
    audio_queue.put(bytes(indata))

# Iniciar la captura de audio
stream = sd.InputStream(
    samplerate=sample_rate,
    blocksize=block_size,
    channels=1,
    dtype='int16',
    callback=audio_callback
)

print("Di algo como: 'Suma 20 y 30' o 'Suma 100 más 100'")

# --- Bucle de escucha con Vosk ---
try:
    with stream:
        while True:
            data = audio_queue.get()
            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                user_input = result.get("text", "").strip()
                
                if user_input:
                    print(f"Texto reconocido: {user_input}")
                    
                    # Enviar el texto a Gemini
                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=user_input,
                        config=config,
                    )
                    
                    # Procesar la respuesta de Gemini
                    if hasattr(response, 'candidates') and response.candidates:
                        candidate = response.candidates[0]
                        if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                            part = candidate.content.parts[0]
                            if hasattr(part, 'function_call'):
                                function_call = part.function_call
                                print(f"Función a llamar: {function_call.name}")
                                print(f"Argumentos: {function_call.args}")
                                
                                # Llamar a la función sumar
                                sumar(**function_call.args)
                            else:
                                print("No se detectó una llamada a función en la respuesta.")
                                print(part.text)
                        else:
                            print("Respuesta inesperada de la API.")
                    else:
                        print("No se recibieron candidatos en la respuesta.")
except KeyboardInterrupt:
    print("\nPrograma terminado por el usuario.")
finally:
    stream.close()