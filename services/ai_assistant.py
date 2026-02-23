from classifier import SimpleNaiveBayes, SEED_DATA
from database.db_core import get_db_connection

# Instancia global del clasificador local Naive Bayes
ai_classifier = SimpleNaiveBayes()

def train_ai_model():
    """Entrena la IA con datos semilla + datos históricos de la DB."""
    try:
        # 1. Entrenar con Semilla (Base Knowledge)
        ai_classifier.train(SEED_DATA)
        print(f"IA: Entrenada con {len(SEED_DATA)} ejemplos semilla.")

        # 2. Entrenar con Datos del Usuario (Incremental Learning)
        conn = get_db_connection()
        tasks = conn.execute("SELECT descripcion, categoria FROM tasks WHERE categoria IS NOT NULL AND categoria != ''").fetchall()
        conn.close()

        user_data = [(t['descripcion'], t['categoria']) for t in tasks]
        if user_data:
            ai_classifier.train(user_data)
            print(f"IA: Refinada con {len(user_data)} tareas históricas.")
        
    except Exception as e:
        print(f"Error entrenando IA: {e}")

def predict_category(descripcion):
    """Clasifica la tarea usando el modelo Naive Bayes."""
    if not descripcion:
        return "General"
    
    # Predicción IA
    prediction = ai_classifier.predict(descripcion)
    return prediction
