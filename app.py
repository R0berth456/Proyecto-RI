import streamlit as st
from PIL import Image
from logica import MotorBusqueda

# Configuración de página
st.set_page_config(page_title="E-Commerce AI", page_icon="🛍️")
st.title("🛍️ Asistente de Compras Inteligente")

# 1. Inicializar el motor (Solo una vez gracias a cache_resource)
@st.cache_resource
def cargar_motor():
    return MotorBusqueda()

try:
    motor = cargar_motor()
except Exception as e:
    st.error(f"Error cargando el sistema. ¿Tienes los archivos en la carpeta 'indices'? Error: {e}")
    st.stop()

# 2. Gestión de Memoria (Session State)
if "mensajes" not in st.session_state:
    st.session_state.mensajes = [] # Historial del chat
if "ultimo_contexto" not in st.session_state:
    st.session_state.ultimo_contexto = [] # Para refinamientos

# 3. Sidebar para subida de imagen (Búsqueda Multimodal)
with st.sidebar:
    st.header("📸 Búsqueda Visual")
    imagen_subida = st.file_uploader("Sube una foto del producto", type=["jpg", "png", "jpeg"])
    btn_buscar_img = st.button("Buscar por Imagen")

# 4. Mostrar Historial del Chat
for msg in st.session_state.mensajes:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        # Si el mensaje tiene imágenes de productos adjuntas
        if "productos" in msg:
            cols = st.columns(len(msg["productos"]))
            for i, p in enumerate(msg["productos"]):
                with cols[i]:
                    if p['image']:
                        st.image(p['image'], width=150)
                    st.caption(f"*{p['name'][:30]}...*")

# --- LÓGICA DE INTERACCIÓN ---

# CASO A: Búsqueda por Imagen
if imagen_subida and btn_buscar_img:
    img = Image.open(imagen_subida)
    st.chat_message("user").image(img, caption="Búsqueda visual", width=200)
    st.session_state.mensajes.append({"role": "user", "content": "Búsqueda por imagen enviada."})
    
    with st.spinner("Analizando imagen y buscando similares..."):
        # Buscar
        resultados = motor.buscar(img, tipo="imagen")
        st.session_state.ultimo_contexto = resultados # Guardar para memoria
        
        # Generar explicación RAG
        respuesta_ia = motor.generar_respuesta(
            "El usuario subió una imagen. Recomienda los productos visualmente similares encontrados.", 
            resultados, 
            st.session_state.mensajes
        )
        
        # Guardar y mostrar respuesta
        msg_ia = {"role": "assistant", "content": respuesta_ia, "productos": resultados}
        st.session_state.mensajes.append(msg_ia)
        st.rerun()

# CASO B: Búsqueda por Texto (Chat)
if prompt := st.chat_input("Escribe qué buscas (ej. 'zapatillas rojas de correr')..."):
    # Mostrar mensaje usuario
    st.chat_message("user").markdown(prompt)
    st.session_state.mensajes.append({"role": "user", "content": prompt})
    
    with st.spinner("Pensando..."):
        # Buscar
        # Nota: Aquí podríamos detectar si es un "refinamiento" usando un LLM, 
        # pero para simplificar, siempre buscamos nuevas opciones o re-rankeamos.
        resultados = motor.buscar(prompt, tipo="texto")
        
        # Generar respuesta RAG con memoria
        respuesta_ia = motor.generar_respuesta(
            prompt, 
            resultados, 
            st.session_state.mensajes
        )
        
        # Mostrar respuesta
        with st.chat_message("assistant"):
            st.markdown(respuesta_ia)
            if resultados:
                st.markdown("---")
                st.write("🔍 *Productos Recomendados:*")
                cols = st.columns(3)
                for i, p in enumerate(resultados[:3]):
                    with cols[i]:
                        if p['image']:
                            st.image(p['image'], use_container_width=True)
                        st.caption(f"{p['name']}\n\n*{p['brand']}*")
        
        # Guardar en historial
        st.session_state.mensajes.append({
            "role": "assistant", 
            "content": respuesta_ia, 
            "productos": resultados[:3]
        })