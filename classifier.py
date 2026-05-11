import re
import math
from collections import defaultdict

class SimpleNaiveBayes:
    def __init__(self):
        self.classes = set()
        self.word_counts = defaultdict(lambda: defaultdict(int))
        self.class_counts = defaultdict(int)
        self.vocab = set()
        self.total_docs = 0
        # Stopwords básicas en español para reducir ruido
        self.stopwords = {
            'el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas', 
            'de', 'del', 'a', 'ante', 'bajo', 'con', 'contra', 'en', 
            'entre', 'hacia', 'hasta', 'para', 'por', 'según', 'sin', 
            'sobre', 'tras', 'y', 'o', 'pero', 'mas', 'mi', 'tu', 'su',
            'que', 'se', 'no', 'si', 'es', 'esta', 'son'
        }

    def _tokenize(self, text):
        # Convertir a minúsculas y extraer solo caracteres alfanuméricos
        words = re.findall(r'\w+', text.lower())
        return [w for w in words if w not in self.stopwords and len(w) > 2]

    def train(self, data):
        """
        Entrena el modelo.
        data: lista de tuplas (texto, categoría)
        """
        for text, category in data:
            if not category or not text:
                continue
            
            self.classes.add(category)
            self.class_counts[category] += 1
            self.total_docs += 1
            
            words = self._tokenize(text)
            for word in words:
                self.vocab.add(word)
                self.word_counts[category][word] += 1

    def predict(self, text):
        if not self.total_docs:
            return "General" # Fallback si no hay entrenamiento

        words = self._tokenize(text)
        best_class = None
        max_prob = -float('inf')

        for category in self.classes:
            # P(Categoria)
            # Log exactitud para evitar underflow numérico
            log_prob = math.log(self.class_counts[category] / self.total_docs)
            
            # P(Palabra | Categoria)
            total_words_in_class = sum(self.word_counts[category].values())
            
            for word in words:
                # Laplace smoothing: (count + 1) / (total + vocab_size)
                count = self.word_counts[category].get(word, 0)
                prob_word_given_class = (count + 1) / (total_words_in_class + len(self.vocab))
                log_prob += math.log(prob_word_given_class)
            
            if log_prob > max_prob:
                max_prob = log_prob
                best_class = category
        
        return best_class if best_class else "General"

# Datos semilla para que el modelo no empiece vacío (Cold Start)
SEED_DATA = [
    # Audiencias
    ("camara gesell audiencia videograbada", "Audiencias"),
    ("camara geselle a las diez", "Audiencias"),
    ("grabar audiencia en sala gesell", "Audiencias"),

    # Impresoras
    ("impresora no imprime", "Impresoras"),
    ("papel atascado bandeja", "Impresoras"),
    ("cambiar toner negro", "Impresoras"),
    ("cartucho vacio", "Impresoras"),
    ("mancha las hojas al imprimir", "Impresoras"),
    ("impresora sin tinta", "Impresoras"),
    
    # Red
    ("no conecta wifi", "Red/Conectividad"),
    ("internet lento", "Red/Conectividad"),
    ("cable de red desconectado", "Red/Conectividad"),
    ("sin acceso a carpeta compartida ip", "Red/Conectividad"),
    ("navegador no carga paginas", "Red/Conectividad"),
    
    # Hardware
    ("monitor no enciende pantalla negra", "Hardware"),
    ("llevar la nueva pc", "Hardware"),
    ("entregar computadora nueva", "Hardware"),
    ("cambiar pc del despacho", "Hardware"),
    ("reemplazar equipo por pc nueva", "Hardware"),
    ("camara no funciona webcam apagada", "Hardware"),
    ("problema con la camara en videollamada", "Hardware"),
    ("microfono no toma audio", "Hardware"),
    ("auriculares no se escuchan", "Hardware"),
    ("scanner no escanea", "Hardware"),
    ("teclado no funciona teclas", "Hardware"),
    ("mouse raton no se mueve", "Hardware"),
    ("cpu hace ruido cooler", "Hardware"),
    ("pc no arranca se apaga", "Hardware"),
    
    # Software
    ("reinstalar la pc", "Software"),
    ("reinstalar windows en la pc", "Software"),
    ("formatear pc e instalar sistema", "Software"),
    ("instalar office word excel", "Software"),
    ("virus antivirus alerta", "Software"),
    ("programa se cierra error", "Software"),
    ("actualizar windows sistema", "Software"),
    ("licencia vencida", "Software"),
    ("hacer backup copia seguridad", "Software"),
    ("respaldo de archivos", "Software"),
    ("formatear pc windows", "Software"),
    
    # Usuarios
    ("olvide clave contraseña usuario", "Usuarios"),
    ("usuario bloqueado dominio", "Usuarios"),
    ("crear nuevo acceso perfil", "Usuarios"),
    ("no puedo entrar al correo", "Usuarios"),
]
