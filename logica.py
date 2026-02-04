import os
import json
import faiss
import numpy as np
from google import genai
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer, CrossEncoder
from PIL import Image

load_dotenv()  # Cargar variables de entorno desde .env

class MotorBusqueda:
    def __init__(self):
        # Configuración de rutas
        self.path_index = "indices/productos.faiss"
        self.path_meta = "indices/metadata.json"
        
        # 1. Cargar Índices Pre-calculados
        print("Cargando índices...")
        self.index = faiss.read_index(self.path_index)
        with open(self.path_meta, 'r') as f:
            self.metadata = json.load(f)
            
        # 2. Cargar Modelos (Solo para codificar la consulta, es rápido)
        print("Cargando modelos...")
        self.encoder = SentenceTransformer("sentence-transformers/clip-vit-b-32-multilingual-v1")
        self.reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2") # Versión Mini es más rápida
        
        # 3. Configurar Gemini (RAG)
        api_key = os.getenv("GOOGLE_API_KEY")
        if api_key:
            self.llm = genai.Client(api_key=api_key)
        else:
            print("ADVERTENCIA: No se encontró GOOGLE_API_KEY")
            self.llm = None

    def buscar(self, consulta, tipo="texto", top_k=20, top_k_rerank=3):
        """Pipeline completo: Recuperación -> Re-ranking -> Contexto"""
        
        # A. Codificar consulta (Texto o Imagen)
        if tipo == "texto":
            vector = self.encoder.encode(consulta)
        else:
            # Asumimos que consulta es un objeto PIL Image
            vector = self.encoder.encode(consulta)
            
        # Normalizar vector
        vector = vector.reshape(1, -1).astype('float32')
        faiss.normalize_L2(vector)
        
        # B. Recuperación Inicial (FAISS)
        distances, indices = self.index.search(vector, top_k)
        
        candidatos = []
        for idx in indices[0]:
            if idx < len(self.metadata):
                candidatos.append(self.metadata[idx])
        
        # C. Re-ranking (Cross-Encoder)
        # Solo aplicamos re-ranking si es búsqueda de texto (Cross-Encoder suele ser texto-texto)
        resultados_finales = candidatos
        if tipo == "texto" and candidatos:
            pairs = [[consulta, f"{c['gender']} {c['category']} {c['subcategory']} {c['product_type']} {c['colour']} {c['usage']} {c['name']}"] for c in candidatos]
            scores = self.reranker.predict(pairs)
            
            # Ordenar por nuevo score
            for i, c in enumerate(candidatos):
                c['score'] = float(scores[i])
            resultados_finales = sorted(candidatos, key=lambda x: x['score'], reverse=True)
        
        return resultados_finales[:top_k_rerank]

    def generar_respuesta(self, consulta, productos, historial=[]):
        """Generación RAG con Gemini"""
        if not self.llm:
            return "Error: API Key no configurada."

        # Construir contexto
        contexto_prods = "\n".join([
            f"- {p['name']} (Category: {p['category']}, Subcategory: {p['subcategory']}, Colour: {p['colour']}, Usage: {p['usage']}, Product_Type: {p['product_type']}, Gender: {p['gender']})."
            for p in productos
        ])
        
        # Historial de chat simple
        chat_context = "\n".join([f"{h['role']}: {h['content']}" for h in historial[-3:]])

        prompt = f"""
        Actúa como un asistente experto de e-commerce.
        
        HISTORIAL DE CONVERSACIÓN:
        {chat_context}
        
        CONSULTA ACTUAL DEL USUARIO: {consulta}
        
        PRODUCTOS ENCONTRADOS (Contexto):
        {contexto_prods}
        
        INSTRUCCIONES:
        1. Recomienda el/los mejor(es) producto(s) de la lista anterior basándote en la consulta.
        2. Justifica tu respuesta usando la información provista (RAG).
        3. Si el usuario pide un cambio (ej. "mejor en rojo"), busca en el contexto si hay algo relevante o explica que estás mostrando las mejores coincidencias visuales/textuales.
        4. Sé amable, breve y persuasivo.
        """
        
        response = self.llm.models.generate_content(model="gemini-3-flash-preview", contents=prompt)
        return response.text