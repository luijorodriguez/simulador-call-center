import streamlit as st
from openai import OpenAI
from gtts import gTTS
import io
from audio_recorder_streamlit import audio_recorder

# Configuración de la página
st.set_page_config(page_title="Simulador de Call Center por Voz", page_icon="🎙️", layout="centered")

st.title("🎙️ Simulador de Llamadas de Voz (Entrenamiento)")
st.caption("Habla por el micrófono para simular la llamada telefónica en tiempo real.")

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

# Cliente OpenRouter con encabezados necesarios
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

# Entrada por texto alternativa
prompt_texto = st.chat_input("O escribe tu mensaje aquí...")

input_usuario = None

if audio_bytes:
    input_usuario = "Hola, buenas tardes, me comunico del centro de atención al cliente."

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

        # Lista de modelos gratuitos activos
        modelos_gratuitos = [
            "google/gemini-2.0-flash-lite-001:free",
            "meta-llama/llama-3.2-1b-instruct:free",
            "meta-llama/llama-3.1-8b-instruct:free",
            "qwen/qwen-2.5-7b-instruct:free",
            "mistralai/mistral-7b-instruct:free"
        ]

        respuesta_ia = None
        errores_detalle = []

        for modelo in modelos_gratuitos:
            try:
                chat_completion = client.chat.completions.create(
                    model=modelo,
                    messages=historial,
                )
                respuesta_ia = chat_completion.choices[0].message.content
                if respuesta_ia:
                    break
            except Exception as e:
                errores_detalle.append(f"• `{modelo}`: {e}")
                continue

        if respuesta_ia:
            st.markdown(respuesta_ia)

            # Convertir texto a voz hablada
            tts = gTTS(text=respuesta_ia, lang='es')
            audio_fp = io.BytesIO()
            tts.write_to_fp(audio_fp)
            audio_fp.seek(0)

            st.audio(audio_fp, format='audio/mp3', autoplay=True)
            st.session_state.messages.append({"role": "assistant", "content": respuesta_ia})
        else:
            st.error("❌ No se pudo conectar con OpenRouter. Detalle del error recibido:")
            for err in errores_detalle[:2]:
                st.write(err)

if st.button("🔴 Finalizar y Reiniciar Llamada"):
    st.session_state.messages = []
    st.rerun()