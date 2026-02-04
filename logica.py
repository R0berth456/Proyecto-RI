import os
import json
import faiss
import numpy as np
import google.generativeai as genai
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer, CrossEncoder
from PIL import Image

load_dotenv()

class MotorBusqueda:
    def __init__(self):
        # Configuración de rutas
        self.path_index = "indices/productos.faiss"
        self.path_meta = "indices/metadata.json"
        
        # 1. Cargar Índices
        print("Cargando índices...")
        try:
            self.index = faiss.read_index(self.path_index)
            with open(self.path_meta, 'r', encoding='utf-8') as f:
                self.metadata = json.load(f)
        except Exception as e:
            print(f"Error fatal cargando índices: {e}")
            self.index = None
            self.metadata = []
            
        # 2. Cargar Modelos
        print("Cargando modelos de IA...")
        # Usamos clip-ViT-B-32 estándar que es más robusto para imágenes
        self.encoder = SentenceTransformer("sentence-transformers/clip-vit-b-32-multilingual-v1")
        self.reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
        
        # 3. Configurar Gemini (RAG)
        api_key = os.getenv("GOOGLE_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            self.llm = genai.GenerativeModel('gemini-1.5-flash')
        else:
            print("ADVERTENCIA: No se encontró GOOGLE_API_KEY en el archivo .env")
            self.llm = None

    def buscar(self, consulta, tipo="texto", top_k=20, top_k_rerank=3):
        """Pipeline: Recuperación -> Re-ranking"""
        if not self.index:
            return []

        # A. Codificar consulta (Texto o Imagen)
        if tipo == "texto":
            vector = self.encoder.encode(consulta)
        else:
            # --- CORRECCIÓN IMPORTANTE PARA IMÁGENES ---
            # 1. Convertir a RGB para evitar errores con PNGs transparentes
            imagen_procesada = consulta.convert("RGB")
            
            # 2. Pasar como LISTA [imagen] para que la librería no intente "leerla" como texto
            vector = self.encoder.encode([imagen_procesada])[0] 
            
        # Normalizar vector (L2 norm) para búsqueda por coseno
        vector = vector.reshape(1, -1).astype('float32')
        faiss.normalize_L2(vector)
        
        # B. Recuperación Inicial (FAISS)
        distances, indices = self.index.search(vector, top_k)
        
        candidatos = []
        # indices[0] porque faiss devuelve una matriz
        for idx in indices[0]:
            if idx != -1 and idx < len(self.metadata): # Chequeo de seguridad
                candidatos.append(self.metadata[idx])
        
        # C. Re-ranking (Cross-Encoder)
        # El Cross-Encoder funciona comparando TEXTO vs TEXTO.
        # Si la búsqueda es por IMAGEN, no podemos usar Cross-Encoder fácilmente 
        # (porque requiere texto del usuario), así que devolvemos los mejores de FAISS directo.
        
        resultados_finales = candidatos
        
        if tipo == "texto" and candidatos:
            # Creamos pares [Consulta, Descripción del producto]
            pairs = []
            for c in candidatos:
                # Construimos una descripción rica para que el modelo entienda
                desc = f"{c.get('name','')} {c.get('category','')} {c.get('colour','')} {c.get('usage','')}"
                pairs.append([consulta, desc])
            
            # Predecir relevancia
            scores = self.reranker.predict(pairs)
            
            # Asignar scores y reordenar
            for i, c in enumerate(candidatos):
                c['score'] = float(scores[i])
            
            # Ordenar de mayor a menor score
            resultados_finales = sorted(candidatos, key=lambda x: x['score'], reverse=True)
        
        return resultados_finales[:top_k_rerank]

    def generar_respuesta(self, consulta, productos, historial=[]):
        """Generación RAG con Gemini"""
        if not self.llm:
            return "Lo siento, no tengo conexión con el cerebro de IA (API Key faltante)."
        
        if not productos:
            return "No encontré productos similares en el catálogo."

        # Construir contexto de productos (Texto enriquecido)
        contexto_prods = "\n".join([
            f"- PRODUCTO: {p.get('name', 'N/A')}\n"
            f"  Detalles: {p.get('category','')} para {p.get('gender','')}, color {p.get('colour','')}.\n"
            f"  Uso: {p.get('usage','')}. Tipo: {p.get('product_type','')}"
            for p in productos
        ])
        
        # Historial (últimos 3 mensajes)
        chat_context = "\n".join([f"{h['role']}: {h['content']}" for h in historial[-3:]])

        prompt = f"""
        Eres un asistente de moda experto y amable (Fashion Stylist).
        
        HISTORIAL RECIENTE:
        {chat_context}
        
        CONSULTA DEL USUARIO: "{consulta}"
        
        HEMOS ENCONTRADO ESTOS PRODUCTOS EN EL CATÁLOGO:
        {contexto_prods}
        
        TU TAREA:
        1. Recomienda el/los mejor(es) producto(s) de la lista anterior basándote en la consulta.
        2. Explica por qué combinan con lo que busca (basado en color, estilo, uso).
        3. Si el usuario pide un cambio (ej. "mejor en rojo"), busca en el contexto si hay algo relevante o explica que estás mostrando las mejores coincidencias visuales/textuales.
        4. Justifica tu respuesta usando la información provista (RAG).
        5. Sé amable, breve y persuasivo.
        3. Si la búsqueda fue por imagen, menciona que encontraste artículos visualmente similares.
        4. Si la consulta actual no tiene relación con los productos, responde educadamente.
        """
        
        try:
            response = self.llm.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Ocurrió un error generando la respuesta: {e}"
