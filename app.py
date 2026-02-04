import streamlit as st
from PIL import Image
import requests
from io import BytesIO
from logica import MotorBusqueda

# Configuración de página
st.set_page_config(page_title="E-Commerce Fashion AI", page_icon="👗", layout="wide")

st.markdown("""
<style>
    .stChatMessage {background-color: #f0f2f6; border-radius: 10px; padding: 10px;}
    .product-card {border: 1px solid #e0e0e0; border-radius: 8px; padding: 10px; margin-bottom: 10px;}
</style>
""", unsafe_allow_html=True)

st.title("👗 Asistente de Moda Inteligente")

# 1. Inicializar el motor
@st.cache_resource
def cargar_motor():
    return MotorBusqueda()

try:
    motor = cargar_motor()
except Exception as e:
    st.error(f"Error cargando el sistema. Verifica que 'productos.faiss' y 'metadata.json' estén en la carpeta 'indices'. Error: {e}")
    st.stop()

# 2. Gestión de Memoria
if "mensajes" not in st.session_state:
    st.session_state.mensajes = [] 

# 3. Sidebar (Búsqueda Visual)
with st.sidebar:
    st.header("📸 Búsqueda Visual")
    st.write("Sube una foto de una prenda para encontrar similares.")
    imagen_subida = st.file_uploader("Subir imagen", type=["jpg", "png", "jpeg"])
    btn_buscar_img = st.button("Buscar por Imagen", use_container_width=True)

# 4. Mostrar Historial
for msg in st.session_state.mensajes:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        
        # Si el mensaje tiene productos adjuntos, mostrarlos en columnas
        if "productos" in msg and msg["productos"]:
            st.markdown("---")
            st.write("found these items:")
            cols = st.columns(3)
            for i, p in enumerate(msg["productos"][:3]): # Mostrar top 3
                with cols[i]:
                    # --- LÓGICA DE IMAGEN CORREGIDA ---
                    img_url = p.get('image_url', '')
                    
                    # Intentar mostrar la imagen desde la URL
                    if img_url:
                        try:
                            st.image(img_url, use_container_width=True)
                        except:
                            st.error("Img no disponible")
                    else:
                        st.text("Sin imagen")
                    
                    # Mostrar metadatos nuevos
                    st.caption(f"**{p.get('name', 'Producto')}**")
                    st.text(f"{p.get('colour', '')} - {p.get('usage', '')}")
                    st.text(f"{p.get('gender', '')} | {p.get('category', '')}")

# --- LÓGICA DE INTERACCIÓN ---

# CASO A: Búsqueda por Imagen
if imagen_subida and btn_buscar_img:
    image = Image.open(BytesIO(imagen_subida.getvalue()))
    st.chat_message("user").image(image, caption="Imagen subida", width=200)
    st.session_state.mensajes.append({"role": "user", "content": "📸 [Imagen subida por el usuario]"})
    
    with st.spinner("Analizando estilo visual..."):
        # Buscar en el motor
        resultados = motor.buscar(image, tipo="imagen")
        
        # Generar texto con Gemini
        respuesta_ia = motor.generar_respuesta(
            "El usuario subió una imagen de una prenda. Recomienda los productos visualmente similares encontrados.", 
            resultados, 
            st.session_state.mensajes
        )
        
        # Guardar respuesta
        st.session_state.mensajes.append({
            "role": "assistant", 
            "content": respuesta_ia, 
            "productos": resultados
        })
        st.rerun()

# CASO B: Búsqueda por Texto
if prompt := st.chat_input("Ej: Vestido rojo de verano para fiesta..."):
    # Mostrar mensaje usuario
    st.chat_message("user").markdown(prompt)
    st.session_state.mensajes.append({"role": "user", "content": prompt})
    
    with st.spinner("Buscando las mejores prendas..."):
        # Buscar
        resultados = motor.buscar(prompt, tipo="texto")
        
        # Generar respuesta
        respuesta_ia = motor.generar_respuesta(prompt, resultados, st.session_state.mensajes)
        
        # Mostrar respuesta inmediata (para efecto de chat fluido)
        with st.chat_message("assistant"):
            st.markdown(respuesta_ia)
            if resultados:
                st.markdown("---")
                cols = st.columns(3)
                for i, p in enumerate(resultados[:3]):
                    with cols[i]:
                        # --- LÓGICA DE IMAGEN CORREGIDA ---
                        if p.get('image_url'):
                            st.image(p['image_url'], use_container_width=True)
                        st.caption(f"**{p.get('name', 'N/A')}**")
                        st.caption(f"*{p.get('usage', '')} - {p.get('colour', '')}*")
        
        # Guardar en historial
        st.session_state.mensajes.append({
            "role": "assistant", 
            "content": respuesta_ia, 
            "productos": resultados
        })