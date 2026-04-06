import os
import json
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

# GROQ API setup
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "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")
client = Groq(api_key=GROQ_API_KEY)

def process_voice_command(text_command=None, audio_path=None):
    """
    Toma un comando (texto o audio) y usa Groq (Whisper + Llama3) 
    para extraer 'descripcion' (tarea) y 'solicitante' (quien lo pidio).
    Devuelve un diccionario.
    """
    try:
        current_text = text_command

        if audio_path:
            print(f"Groq Processing Audio: {audio_path}")
            with open(audio_path, "rb") as file:
                # Transcripcion usando Whisper de Groq (Extra rápido)
                transcription = client.audio.transcriptions.create(
                  file=(os.path.basename(audio_path), file.read()),
                  model="whisper-large-v3", # Modelo de vanguardia para español
                  prompt="El audio trata sobre soporte técnico, impresoras, computadoras y redes en español.",
                  response_format="json",
                  language="es",
                  temperature=0.0
                )
                current_text = transcription.text
            
            print(f"Texto extraído por Whisper-Groq: {current_text}")

        if not current_text or current_text.strip() == "":
            raise Exception("No se obtuvo texto del comando de audio.")

        # Extraer entidades con Llama-3.3 70B (Velocidad instantánea y altísima precisión)
        prompt = f"""
Actúas como un asistente de inventario y tareas técnicas corporativas.
Se te dará un texto dictado por un técnico. 
Extrae o deduce estrictamente 2 campos:
1) "descripcion": El problema o acción a realizar. 
2) "solicitante": La persona, área o juez que pide el trabajo. Si no se menciona, déjalo vacío "".

Ejemplo 1: "La jueza martinez tiene problema con la impresora en la vocalía 2"
Respuesta: {{"descripcion": "problema con la impresora en la vocalía 2", "solicitante": "jueza martinez"}}

Responde EXCLUSIVAMENTE con un JSON puro con esas dos claves.

Texto a analizar: "{current_text}"
"""
        
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "user", "content": prompt}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.0,
            # Aseguramos que devuelva JSON
            response_format={"type": "json_object"}
        )
        
        raw_text = chat_completion.choices[0].message.content.strip()
        print(f"Groq Llama-3 Response: {raw_text}")
        
        return json.loads(raw_text)

    except Exception as e:
        # LOGEAR ERROR A ARCHIVO PARA DEPURAR
        import datetime
        os.makedirs("logs", exist_ok=True)
        with open("logs/voice_debug.log", "a", encoding="utf-8") as logf:
            logf.write(f"[{datetime.datetime.now()}] FATAL GROQ AI: {str(e)}\n")

        print(f"Error AI MultiModal Groq: {e}")
        return {
            "descripcion": text_command or "Error al procesar audio. Intenta de nuevo.",
            "solicitante": ""
        }
