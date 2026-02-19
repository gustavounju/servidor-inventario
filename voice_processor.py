
import os
import json
import google.generativeai as genai

# API KEY PROPORCIONADA POR EL USUARIO
API_KEY = "AIzaSyDFYACcXHnLRNp1nrcr272MnQs5KRR7hIE"

def process_voice_command(text_command):
    """
    Usa Gemini Flash para extraer (descripcion, solicitante) de un texto de voz desordenado.
    """
    try:
        genai.configure(api_key=API_KEY)
        # Using the specific stable model version
        model = genai.GenerativeModel('gemini-1.5-flash')

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

        print(f"IA Processing: {text_command}")
        response = model.generate_content(prompt)
        
        # Limpiar respuesta (a veces pone ```json ... ```)
        raw_text = response.text.strip()
        print(f"IA Raw Response: {raw_text}")
        
        if raw_text.startswith("```json"):
            raw_text = raw_text.replace("```json", "").replace("```", "")
        
        data = json.loads(raw_text)
        return data

    except Exception as e:
        print(f"Error AI: {e}")
        # Fallback: devolver todo como descripción
        return {
            "descripcion": text_command,
            "solicitante": ""
        }
