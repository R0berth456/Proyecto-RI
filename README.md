# 👗 Asistente de Moda Inteligente - E-Commerce Fashion AI

Un asistente inteligente de moda basado en IA que permite búsquedas de productos tanto por texto como por imágenes. Combina tecnologías avanzadas de visión por computadora, procesamiento de lenguaje natural y recuperación de información para proporcionar recomendaciones personalizadas.

## 🎯 Características Principales

- **Búsqueda por Texto**: Realiza consultas en lenguaje natural (ej: "Vestido rojo de verano para fiesta")
- **Búsqueda Visual**: Sube una imagen para encontrar prendas visualmente similares
- **Recomendaciones Inteligentes**: Usa Gemini AI para generar recomendaciones personalizadas
- **Re-ranking Automático**: Prioriza los resultados más relevantes usando CrossEncoder
- **Historial de Conversación**: Mantiene el contexto de tus búsquedas anteriores
- **Interfaz Amigable**: Aplicación web interactiva construida con Streamlit

## 🛠️ Tecnologías Utilizadas

- **Streamlit**: Framework web interactivo para Python
- **FAISS**: Búsqueda eficiente de similitud vectorial
- **SentenceTransformers (CLIP)**: Embeddings de texto e imágenes
- **CrossEncoder**: Re-ranking de resultados
- **Google Generative AI (Gemini)**: Generación de recomendaciones inteligentes
- **PIL**: Procesamiento de imágenes
- **Dotenv**: Gestión de variables de entorno

## 📋 Requisitos Previos

- Python 3.8 o superior
- Cuenta de Google Cloud con API habilitada (Generative AI)
- Indices FAISS y metadatos precargados (`indices/productos.faiss` y `indices/metadata.json`)

## 🚀 Instalación

### 1. Clonar el repositorio
```bash
git clone <tu-repositorio>
cd Proyecto-RI
```

### 2. Crear un entorno virtual
```bash
python -m venv env
```

### 3. Activar el entorno virtual

**Windows:**
```bash
env\Scripts\activate
```

**Linux/Mac:**
```bash
source env/bin/activate
```

### 4. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 5. Configurar la API Key
Crea un archivo `.env` en la raíz del proyecto:
```env
GOOGLE_API_KEY=tu_clave_api_aqui
```

## 💻 Uso

### Ejecutar la aplicación
```bash
streamlit run app.py
```

La aplicación se abrirá en `http://localhost:8501`

### Tipos de Búsqueda

**Búsqueda por Texto:**
- Escribe lo que buscas en el chat (ej: "Sudadera gris para hombre")
- El asistente busca productos relacionados y proporciona recomendaciones

**Búsqueda Visual:**
- En la barra lateral, sube una imagen de una prenda
- Haz clic en "Buscar por Imagen"
- El sistema encontrará prendas visualmente similares

## 📁 Estructura del Proyecto

```
Proyecto-RI/
├── app.py              # Aplicación principal (UI con Streamlit)
├── logica.py           # Lógica del motor de búsqueda y IA
├── requirements.txt    # Dependencias del proyecto
├── .env               # Variables de entorno (crear manualmente)
├── .gitignore         # Archivos a ignorar en git
├── indices/           # Índices y metadatos FAISS
│   ├── productos.faiss    # Índice vectorial de productos
│   └── metadata.json      # Metadatos de productos
└── env/               # Entorno virtual Python

```

## 🧠 Cómo Funciona

### Pipeline de Búsqueda

1. **Codificación**: El texto o imagen se convierte en un vector usando CLIP (SentenceTransformers)
2. **Recuperación**: Se buscan los 20 productos más similares usando FAISS
3. **Re-ranking**: Los resultados se ordenan por relevancia usando CrossEncoder
4. **Generación**: Gemini genera una recomendación personalizada basada en los resultados

### Clases Principales

**MotorBusqueda** (`logica.py`):
- `buscar()`: Realiza búsquedas de texto o imagen
- `generar_respuesta()`: Genera recomendaciones usando RAG (Retrieval-Augmented Generation)

## 📊 Estructura de Metadatos

Cada producto en `metadata.json` contiene:
```json
{
  "name": "Nombre del Producto",
  "category": "Categoría",
  "colour": "Color",
  "usage": "Uso/Ocasión",
  "gender": "Género",
  "product_type": "Tipo de Producto",
  "image_url": "URL de la imagen"
}
```

## ⚙️ Configuración

### Variables de Entorno

- `GOOGLE_API_KEY`: Tu API key de Google Generative AI (obligatoria)

### Hiperparámetros Ajustables

En `logica.py`, método `buscar()`:
- `top_k`: Número de candidatos iniciales (default: 20)
- `top_k_rerank`: Número de resultados finales (default: 3)

En `app.py`, visualización:
- Número de columnas para mostrar productos (default: 3)

## 🐛 Solución de Problemas

**Error: "Error cargando el sistema. Verifica que 'productos.faiss' y 'metadata.json' estén en la carpeta 'indices'"**
- Asegúrate de que la carpeta `indices/` contiene ambos archivos
- Verifica que los archivo tienen los nombres exactos

**Error: "ADVERTENCIA: No se encontró GOOGLE_API_KEY"**
- Crea un archivo `.env` con tu API key
- Obtén la clave en https://console.cloud.google.com/

**La búsqueda por imagen no muestra resultados**
- Verifica que la imagen está en formato JPG, PNG o JPEG
- Intenta con una imagen más clara de una prenda de ropa
