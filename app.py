import streamlit as st
from groq import Groq
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
    
    api_key_input = st.text_input("Groq API Key (Empieza con gsk_):", type="password")
    api_key = api_key_input.strip() if api_key_input else ""
    
    rol_ia = st.selectbox("Rol de la IA:", ["Cliente (Usuario es Operador)", "Operador (Usuario es Cliente)"])
    
    st.markdown("---")
    st.subheader("📚 Base de Conocimiento / Manual")
    manual_context = st.text_area(
        "Ingresa las políticas o guion del call center:",
        value="El cliente llama porque no reconoce un cobro de $50 en su estado de cuenta. El operador debe pedir número de cédula, validar identidad, mostrar empatía y aplicar la política de reembolso automático si es menor a $100.",
        height=180
    )

# Inicializar historial
if "messages" not in st.session_state:
    st.session_state.messages = []

# Validar API Key
if not api_key:
    st.info("💡 Ingresa tu Groq API Key en el panel izquierdo. Es 100% gratuita en console.groq.com")
    st.stop()

# Cliente de Groq
client = Groq(api_key=api_key)

# System Prompt
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

# Grabador de Audio
audio_bytes = audio_recorder(
    text="Presiona para Grabar",
    recording_color="#e8b62c",
    neutral_color="#6aa36f",
    icon_size="2x"
)

if audio_bytes:
    # 1. Transcribir Voz a Texto con Groq Whisper
    with st.spinner("Escuchando y procesando tu voz..."):
        try:
            transcription = client.audio.transcriptions.create(
                file=("audio.wav", audio_bytes),
                model="whisper-large-v3-turbo",
                language="es"
            )
            user_text = transcription.text
        except Exception as e:
            st.error(f"Error al procesar el audio: {e}")
            st.stop()

    if user_text:
        # Guardar y mostrar mensaje del usuario
        st.session_state.messages.append({"role": "user", "content": user_text})
        with st.chat_message("user"):
            st.markdown(user_text)

        # 2. Generar Respuesta con Llama 3.3
        with st.chat_message("assistant"):
            historial = [{"role": "system", "content": prompt_sistema}]
            for m in st.session_state.messages:
                historial.append({"role": m["role"], "content": m["content"]})

            try:
                chat_completion = client.chat.completions.create(
                    messages=historial,
                    model="llama-3.3-70b-versatile",
                    temperature=0.7
                )
                respuesta_ia = chat_completion.choices[0].message.content
                st.markdown(respuesta_ia)

                # 3. Convertir Texto a Voz (audio respuesta)
                tts = gTTS(text=respuesta_ia, lang='es')
                audio_fp = io.BytesIO()
                tts.write_to_fp(audio_fp)
                audio_fp.seek(0)

                # Reproducir audio automáticamente
                st.audio(audio_fp, format='audio/mp3', autoplay=True)

                st.session_state.messages.append({"role": "assistant", "content": respuesta_ia})

            except Exception as e:
                st.error(f"Error al generar respuesta: {e}")

# Botón para reiniciar
if st.button("🔴 Finalizar y Reiniciar Llamada"):
    st.session_state.messages = []
    st.rerun()