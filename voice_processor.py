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
        Actúa como un asistente de inventario experto para soporte técnico.
        Tu misión es corregir errores fonéticos comunes y estructurar la orden.
        
        Contexto conocido (Nombres y Lugares probables):
        - Dr. Granados
        - Dra. Berta
        - Secretaria Patricia
        - Contabilidad, Recepción, Gerencia
        - "Autor ganado" -> Dr. Granados (Error cómun)

        Analiza el siguiente comando de voz (que puede tener errores de transcripción) y extrae:
        1. "descripcion": Qué tarea hay que hacer. Corrigiendo errores obvios (ej: "teclado" es teclado).
           Si menciona "fui a ver/revisar", la tarea es "Revisar/Reparar [objeto]".
        2. "solicitante": Quién lo pidió o de quién es la máquina.
        
        Texto original: "{text_command}"
        
        Responde SOLO con un JSON válido:
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
