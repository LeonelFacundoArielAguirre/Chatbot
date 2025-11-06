import streamlit as st  # Ya fue instalado
import groq  # Ya fue instalado
from pathlib import Path
from typing import Optional

# Configuración inicial de la página (debe ir al principio)
st.set_page_config(page_title="Misterio", page_icon="❓")

# Intentamos usar tomllib (python 3.11+). Si no está, usamos la biblioteca 'toml' si está instalada.
try:
    import tomllib  # type: ignore
except Exception:
    try:
        import toml as tomllib  # type: ignore
    except Exception:
        tomllib = None


def load_streamlit_config() -> dict:
    """Lee `.streamlit/config.toml` y devuelve un dict.

    Retorna {} si no existe el archivo o no hay parser disponible.
    """
    cfg_path = Path(__file__).parent / ".streamlit" / "config.toml"
    if not cfg_path.exists():
        return {}
    if tomllib is None:
        # No podemos leer el TOML porque no hay parser instalado
        st.warning("No se encontró 'tomllib' ni 'toml'. No se puede leer .streamlit/config.toml desde el código.")
        return {}

    # tomllib.load acepta un archivo en modo binario (Python 3.11+). La lib 'toml' usa texto.
    try:
        # Abrimos en binario y probamos tomllib.load (funciona con tomllib real)
        with cfg_path.open('rb') as f:
            try:
                cfg = tomllib.load(f)  # tomllib
            except Exception:
                # fallback: leer como texto y usar loads (funciona con la lib 'toml')
                f.seek(0)
                text = f.read().decode('utf-8')
                cfg = tomllib.loads(text)
    except Exception:
        return {}

    return cfg

def crear_usuario_groq() -> groq.Client:
    """Crea y retorna un cliente de Groq usando la clave API desde st.secrets."""
    clave_secreta = st.secrets["CLAVE_API"]
    return groq.Client(api_key=clave_secreta)

MODELOS = ['llama-3.1-8b-instant', 'llama-3.3-70b-versatile', 'deepseek-r1-distill-llama-70b']

def configurar_modelo(cliente: groq.Client, modelo: str, mensaje_entrada: str):
    """Configura y retorna una llamada al modelo de Groq."""
    return cliente.chat.completions.create(
        model=modelo,
        messages=[{"role": "user", "content": mensaje_entrada}],
        stream=True
    )

def inicializar_estado():
    """Inicializa el estado de la sesión si no existe."""
    if "mensajes" not in st.session_state:
        st.session_state.mensajes = []

def area_chat():
    """Muestra el área de chat con el historial de mensajes."""
    for mensaje in st.session_state.mensajes:
        with st.chat_message(mensaje["role"]):
            st.write(mensaje["content"])

def actualizar_historial(role: str, content: str, name: Optional[str] = None):
    """Actualiza el historial de chat con un nuevo mensaje."""
    st.session_state.mensajes.append({
        "role": role,
        "content": content,
        "name": name
    })
def main():
    """Función principal de la aplicación."""
    st.title("Misterio")
    st.write("El Chatbot llamado 'Misterio', funciona con Groq y Streamlit")

    # Configuración inicial
    elegir_modelo = st.sidebar.selectbox("Selecciona el modelo de lenguaje:", MODELOS)
    cliente_usuario = crear_usuario_groq()
    inicializar_estado()

    # Cargamos el archivo de config de Streamlit (si existe)
    _streamlit_cfg = load_streamlit_config()
    if _streamlit_cfg:
        primary = _streamlit_cfg.get('primaryColor')
        if primary:
            st.markdown(f"**Color primario en config:** `{primary}`")

    # Mostramos el historial de chat
    area_chat()

    # Input del usuario y procesamiento
    mensaje = st.chat_input("Escribí tu mensaje:")
    if mensaje:
        actualizar_historial("user", mensaje, "")
        chat_respuesta = configurar_modelo(cliente_usuario, elegir_modelo, mensaje)
        
        # Procesamos la respuesta del modelo (stream=True)
        respuesta_completa = []
        for chunk in chat_respuesta:
            if chunk.choices[0].delta.content:
                respuesta_completa.append(chunk.choices[0].delta.content)
        
        respuesta = "".join(respuesta_completa)
        actualizar_historial("assistant", respuesta, "")
        st.rerun()

if __name__ == "__main__":
    main()