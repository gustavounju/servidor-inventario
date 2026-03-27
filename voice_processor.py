import os
import json
from google import genai

def process_voice_command(text_command):
    """
    Usa Gemini Flash para extraer (descripcion, solicitante) de un texto de voz desordenado.
    """
    try:
        # Obtener clave API de forma remota y segura (Variables de entorno)
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("Falta configurar la variable de entorno GEMINI_API_KEY en el servidor")

        client = genai.Client(api_key=api_key)
        
        prompt = f"""
Eres un asistente de soporte técnico informático. Tu única función es analizar frases dictadas por voz y extraer dos campos.

REGLAS IMPORTANTES:
1. "solicitante": La persona o cargo que tiene el problema o que lo pidió. 
   - Si la frase empieza con "el contador", "la doctora", "secretaría", etc. → ese es el SOLICITANTE.
   - Ejemplos: "el contador tiene problema" → solicitante: "Contador"
               "la secretaria pide revisar" → solicitante: "Secretaria"
               "fui a ver a Berta" → solicitante: "Berta"
2. "descripcion": El problema o tarea en sí, SIN mencionar al solicitante.
   - Ejemplos: "tiene problema con un cartucho" → "Problema con cartucho"
               "pide revisar la impresora" → "Revisar impresora"
               "no enciende la PC" → "PC no enciende"

CORRECCIONES FOFONÉTICAS COMUNES:
- "autor ganado" → Dr. Granados
- "contaduría" / "el contador" → Contaduría / Contador  
- "secretaria" → Secretaria
- "cartucho" → cartucho (de impresora)

Texto dictado: "{text_command}"

Responde SOLO con JSON válido, sin explicaciones:
{{
    "descripcion": "...",
    "solicitante": "..."
}}
"""

        print(f"IA Processing (New SDK): {text_command}")
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        
        raw_text = response.text.strip()
        print(f"IA Raw Response: {raw_text}")
        
        # Limpiar bloques de código markdown si existen
        if raw_text.startswith("```json"):
            raw_text = raw_text.replace("```json", "", 1)
        if raw_text.startswith("```"):
            raw_text = raw_text.replace("```", "", 1)
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]
        
        data = json.loads(raw_text)
        return data

    except Exception as e:
        print(f"Error AI: {e}")
        # Fallback: devolver todo como descripción
        return {
            "descripcion": text_command,
            "solicitante": ""
        }
