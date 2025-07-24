# 📷 Camera Controller  

*Project developed by Adakademy students*  
A voice-controlled camera system using Vosk (speech recognition), Gemini (generative AI), and OpenCV (image processing).  

---

## 🧭 Index  
- [Overview](#-overview)  
- [Requirements](#-requirements)  
- [Tools & Usage](#-tools_and_usuage)  
  - [Vosk](#-vosk)  
  - [OpenCV](#-opencv_(image_processing))  
  - [Gemini](#Gemini)
  - [Pygame](#pygame)  
  - [Sounddevice](#sounddevice)  
---

## 🌍 Overview  
This project, created by **Adakademy students**, enables hands-free camera control through **voice commands** (Vosk), real-time **image analysis** (OpenCV), and **AI-powered interactions** (Gemini). Ideal for automation, security, or accessibility applications.  

---

## 📋 Requirements  
To run the project, you need:  
- **Python 3.10+** (recommended).  
- Libraries:  
  ```bash
  pip installrrequiremets.txt
- **It must need a camera**.

---
## 🕵️‍♂️ Tools and usuage

**Vosk**:

Features:

Offline Speech-to-Text:
          
  - Loads language models (e.g., vosk-model-es-0.42 for Spanish).

  - Processes audio in real-time using KaldiRecognizer.

Audio Stream Handling:

  -  Integrates with sounddevice to capture microphone input.

  -  Uses AcceptWaveform() and PartialResult() for incremental recognition.

Language Support:

  - Configurable language models (e.g., lang="es").

Example:

    model = Model("modelos/vosk-model-es-0.42")  # Load model
      recognizer = KaldiRecognizer(model, 16000)   # 16kHz sample rate
      if recognizer.AcceptWaveform(data):          # Process audio chunks
              text = json.loads(recognizer.Result())["text"]

---

**OpenCV (Image Processing)**:
      
Features:

Color Detection:
          
  -  Converts BGR to HSV/LAB color spaces for robust detection.

  -  Uses cv2.inRange() to create masks for specific colors.
 
Morphological operations:

  -  Applies erosion/dilation (cv2.erode(), cv2.dilate()) to clean masks.

Contour detection:

  - Finds object boundaries with cv2.findContours().

Camera Integration:

  -  Captures frames via cv2.VideoCapture(0).

Example:

      hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)          # Convert color space
      mask = cv2.inRange(hsv, lower_range, upper_range)     # Create mask
      contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)  # Detect objects

---

**Gemini (Generative AI)**

Features:

Function Calling:

  -  Declares custom functions (e.g., sumar_numeros, dividir_numeros) with descriptions/parameters.

  -  Parses natural language into structured calls (e.g., "Suma 5 y 3" → sumar_numeros(5, 3)).

Text Generation:

  -  Uses gemini-2.5-flash model for low-latency responses.

Tool Configuration:

  -  GenerateContentConfig links Gemini to custom tools.

Example: 

    
    
    sumar_tool = types.FunctionDeclaration(
      name="sumar_numeros",
      description="Suma dos números",
      parameters={"num1": {"type": "number"}, "num2": {"type": "number"}}
    )
    response = client.generate_content(
       model="gemini-2.5-flash", 
       contents="Suma 10 y 20", 
       config=config
    )

---


**Pygame (Audio/UI)**:

Features:

Audio Playback:

   -  Plays generated speech (via gTTS) using pygame.mixer.

Temporary File Handling:

   -  Creates/deletes MP3 files for TTS dynamically.

Basic UI:

   -  Displays sliders/buttons for color range tuning (in OpenCV example).

Example: 

        mixer.init()                          # Initialize audio
        mixer.music.load("temp.mp3")          # Load TTS file
        mixer.music.play()                    # Play audio
        while mixer.music.get_busy():         # Wait for playback
        time.sleep(0.05)

---

**Sounddevice (Audio Capture)**:

Features:

Real-Time Microphone Input:

  -  Records audio in chunks (e.g., blocksize=8000) at 16kHz.

Queue-Based Processing:

  -  Buffers audio data for Vosk using a queue.Queue.

Cross-Platform:

  -  Works on Windows/macOS/Linux.

Example:

    def callback(indata, frames, time, status):
    audio_queue.put(bytes(indata))  # Send audio to queue

    stream = sd.InputStream(
        samplerate=16000, 
        callback=callback, 
        dtype="int16"
    )
