import streamlit as st
from openai import OpenAI
from gtts import gTTS
import io
import json
import urllib.request
import speech_recognition as sr
from audio_recorder_streamlit import audio_recorder

# Configuración de la página
st.set_page_config(page_title="Simulador de Call Center por Voz", page_icon="🎙️", layout="centered")

st.title("🎙️ Simulador de Llamadas de Voz (Entrenamiento)")
st.caption("Habla por el micrófono para simular la llamada telefónica en tiempo real.")

# Función para transcribir voz a texto de forma gratuita
def transcribir_audio(audio_bytes):
    r = sr.Recognizer()
    audio_file = io.BytesIO(audio_bytes)
    try:
        with sr.AudioFile(audio_file) as source:
            audio_data = r.record(source)
            texto = r.recognize_google(audio_data, language="es-ES")
            return texto
    except sr.UnknownValueError:
        st.warning("⚠️ No se entendió el audio. Intenta hablar más claro o cerca del micrófono.")
        return None
    except Exception as e:
        st.error(f"❌ Error procesando el audio: {e}")
        return None

# Función que consulta la lista de modelos GRATUITOS en vivo
@st.cache_data(ttl=3600)
def obtener_modelos_gratuitos_en_vivo():
    try:
        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/models",
            headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            data_list = data.get("data", [])
            modelos_free = [item["id"] for item in data_list if item.get("id", "").endswith(":free")]
            if modelos_free:
                return modelos_free
    except Exception:
        pass
    
    return [
        "meta-llama/llama-3.1-8b-instruct:free",
        "mistralai/mistral-7b-instruct:free",
        "qwen/qwen-2.5-72b-instruct:free"
    ]

# Sidebar - Configuración
with st.sidebar:
    st.header("⚙️ Configuración del Simulador")
    api_key_input = st.text_input("OpenRouter API Key (sk-or-v1-...):", type="password")
    api_key = api_key_input.strip() if api_key_input else ""
    rol_ia = st.selectbox("Rol de la IA:", ["Cliente (Usuario es Operador)", "Operador (Usuario es Cliente)"])
    st.markdown("---")
    manual_context = st.text_area(
        "Ingresa las políticas o guion del call center:",
        value="El cliente llama porque no reconoce un cobro de $50 en su estado de cuenta. El operador debe pedir número de cédula, validar identidad, mostrar empatía y aplicar la política de reembolso automático si es menor a $100.",
        height=180
    )

if "messages" not in st.session_state:
    st.session_state.messages = []

if not api_key:
    st.info("💡 Ingresa tu OpenRouter API Key en el panel izquierdo. Es gratuita en openrouter.ai")
    st.stop()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
    default_headers={
        "HTTP-Referer": "https://streamlit.io",
        "X-Title": "Simulador Call Center"
    }
)

prompt_sistema = f"""
Eres un participante en un simulador de entrenamiento para un call center telefónico.
Tu rol actual es: {rol_ia}.
Debes seguir estrictamente este contexto y manual:
---
{manual_context}
---
Instrucciones críticas:
1. Habla de forma natural e hiperrealista, acorde a tu rol.
2. Mantén tus respuestas MUY BREVES (máximo 1 a 2 oraciones sencillas), para que la conversación fluya como una llamada real.
3. No uses texto entre paréntesis ni acotaciones como (suspirando) o [molesto].
"""

# Mostrar historial
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

st.markdown("---")
st.write("👇 **Toca el micrófono para hablar y vuelve a tocarlo para detenerte:**")

audio_bytes = audio_recorder(
    text="Presiona para Grabar",
    recording_color="#e8b62c",
    neutral_color="#6aa36f",
    icon_size="2x"
)

prompt_texto = st.chat_input("O escribe tu mensaje aquí...")

input_usuario = None

# Procesar audio real solo si es una grabación nueva
if audio_bytes and ("last_audio" not in st.session_state or st.session_state.last_audio != audio_bytes):
    st.session_state.last_audio = audio_bytes
    with st.spinner("🎙️ Transcribiendo tu voz..."):
        input_usuario = transcribir_audio(audio_bytes)

if prompt_texto:
    input_usuario = prompt_texto

if input_usuario:
    st.session_state.messages.append({"role": "user", "content": input_usuario})
    with st.chat_message("user"):
        st.markdown(input_usuario)

    with st.chat_message("assistant"):
        historial = [{"role": "system", "content": prompt_sistema}]
        for m in st.session_state.messages:
            historial.append({"role": m["role"], "content": m["content"]})

        modelos_gratuitos = obtener_modelos_gratuitos_en_vivo()
        respuesta_ia = None

        for modelo in modelos_gratuitos:
            try:
                chat_completion = client.chat.completions.create(
                    model=modelo,
                    messages=historial,
                )
                respuesta_ia = chat_completion.choices[0].message.content
                if respuesta_ia:
                    break
            except Exception:
                continue

        if respuesta_ia:
            st.markdown(respuesta_ia)

            # Convertir respuesta a voz y reproducir
            tts = gTTS(text=respuesta_ia, lang='es')
            audio_fp = io.BytesIO()
            tts.write_to_fp(audio_fp)
            audio_fp.seek(0)

            st.audio(audio_fp, format='audio/mp3', autoplay=True)
            st.session_state.messages.append({"role": "assistant", "content": respuesta_ia})
        else:
            st.error("❌ No se pudo obtener respuesta de los modelos gratuitos.")

if st.button("🔴 Finalizar y Reiniciar Llamada"):
    st.session_state.messages = []
    if "last_audio" in st.session_state:
        del st.session_state["last_audio"]
    st.rerun()