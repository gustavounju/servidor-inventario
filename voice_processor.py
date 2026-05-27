import os
import json
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

# GROQ API setup — la clave DEBE estar en el archivo .env como GROQ_API_KEY
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
if not GROQ_API_KEY:
    raise EnvironmentError("GROQ_API_KEY no está definida en el archivo .env. El procesador de voz no puede iniciar.")
client = Groq(api_key=GROQ_API_KEY)


def process_voice_command(text_command=None, audio_path=None):
    """
    Toma un comando (texto o audio) y usa Groq (Whisper + Llama3)
    para extraer descripcion, solicitante, estado de cierre y solucion.
    Devuelve un diccionario.
    """
    try:
        current_text = text_command

        if audio_path:
            print(f"Groq Processing Audio: {audio_path}")
            with open(audio_path, "rb") as file:
                transcription = client.audio.transcriptions.create(
                    file=(os.path.basename(audio_path), file.read()),
                    model="whisper-large-v3",
                    prompt="El audio trata sobre soporte tecnico, impresoras, computadoras y redes en espanol.",
                    response_format="json",
                    language="es",
                    temperature=0.0,
                )
                current_text = transcription.text

            print(f"Texto extraido por Whisper-Groq: {current_text}")

        if not current_text or current_text.strip() == "":
            raise Exception("No se obtuvo texto del comando de audio.")

        prompt = f"""
Actuas como un asistente de inventario y tareas tecnicas corporativas.
Se te dara un texto dictado por un tecnico.
Extrae o deduce estrictamente estos campos:
1) "descripcion": El problema o accion a realizar.
2) "solicitante": La persona, area o juez que pide el trabajo. Si no se menciona, dejalo vacio "".
3) "is_done": true si el texto indica que la tarea ya fue hecha, resuelta, finalizada, reparada o solucionada; si no, false.
4) "solucion": como se resolvio, solo si se menciona o puede deducirse claramente. Si no, dejalo vacio "".

Ejemplo 1: "La jueza martinez tiene problema con la impresora en la vocalia 2"
Respuesta: {{"descripcion": "problema con la impresora en la vocalia 2", "solicitante": "jueza martinez", "is_done": false, "solucion": ""}}

Ejemplo 2: "Ya arregle la impresora de mesa de entradas, era el cable USB flojo, lo pidio Laura"
Respuesta: {{"descripcion": "impresora de mesa de entradas", "solicitante": "Laura", "is_done": true, "solucion": "Se ajusto el cable USB flojo"}}

Responde EXCLUSIVAMENTE con un JSON puro con esas cuatro claves.

Texto a analizar: "{current_text}"
"""

        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "user", "content": prompt}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.0,
            response_format={"type": "json_object"},
        )

        raw_text = chat_completion.choices[0].message.content.strip()
        print(f"Groq Llama-3 Response: {raw_text}")

        result = json.loads(raw_text)
        result.setdefault("descripcion", "")
        result.setdefault("solicitante", "")
        result.setdefault("is_done", False)
        result.setdefault("solucion", "")
        if isinstance(result["is_done"], str):
            result["is_done"] = result["is_done"].strip().lower() in ("true", "1", "si", "yes")
        return result

    except Exception as e:
        import datetime

        os.makedirs("logs", exist_ok=True)
        with open("logs/voice_debug.log", "a", encoding="utf-8") as logf:
            logf.write(f"[{datetime.datetime.now()}] FATAL GROQ AI: {str(e)}\n")

        print(f"Error AI MultiModal Groq: {e}")
        return {
            "descripcion": text_command or "Error al procesar audio. Intenta de nuevo.",
            "solicitante": "",
            "is_done": False,
            "solucion": "",
        }
