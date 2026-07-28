import streamlit as st
from openai import OpenAI
from gtts import gTTS
import io
import json
import urllib.request
import speech_recognition as sr
from audio_recorder_streamlit import audio_recorder

# Configuración de la página
st.set_page_config(page_title="Simulador de Call Center con Evaluación", page_icon="📞", layout="centered")

st.title("📞 Simulador de Llamadas de Entrenamiento")
st.caption("Entorno interactivo por voz con auditoría de desempeño en tiempo real.")

# Inicializar estados de la sesión
if "messages" not in st.session_state:
    st.session_state.messages = []
if "evaluado" not in st.session_state:
    st.session_state.evaluado = False
if "evaluacion_texto" not in st.session_state:
    st.session_state.evaluacion_texto = ""

# Función para transcribir voz a texto
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
Debes seguir strictly este contexto y manual:
---
{manual_context}
---
Instrucciones críticas:
1. Habla de forma natural e hiperrealista, acorde a tu rol.
2. Mantén tus respuestas MUY BREVES (máximo 1 a 2 oraciones sencillas), para que la conversación fluya como una llamada real.
3. No uses texto entre paréntesis ni acotaciones.
"""

# Mostrar historial de la llamada
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ---------------------------------------------------------
# MODO 1: LLAMADA EN CURSO (SI AÚN NO SE HA EVALUADO)
# ---------------------------------------------------------
if not st.session_state.evaluado:
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

                tts = gTTS(text=respuesta_ia, lang='es')
                audio_fp = io.BytesIO()
                tts.write_to_fp(audio_fp)
                audio_fp.seek(0)

                st.audio(audio_fp, format='audio/mp3', autoplay=True)
                st.session_state.messages.append({"role": "assistant", "content": respuesta_ia})

    st.markdown("---")
    # BOTÓN PARA FINALIZAR Y EVALUAR
    if st.button("🔴 Finalizar Llamada y Evaluar Desempeño", use_container_width=True):
        if len(st.session_state.messages) < 2:
            st.warning("⚠️ Debes interactuar en la llamada antes de solicitar una evaluación.")
        else:
            with st.spinner("📊 Auditando la gestión con la Base de Conocimiento..."):
                # Transcripción completa de la llamada
                transcripcion = ""
                for msg in st.session_state.messages:
                    rol = "OPERADOR" if msg["role"] == "user" else "CLIENTE"
                    transcripcion += f"{rol}: {msg['content']}\n"

                prompt_evaluacion = f"""
                Eres un Auditor de Calidad Senior de Call Center.
                Evalúa la siguiente llamada entre el Operador y el Cliente basándote estrictamente en estas políticas y manuales de la empresa:
                
                MANUAL Y POLÍTICAS DE LA EMPRESA:
                ---
                {manual_context}
                ---
                
                TRANSCRIPCIÓN COMPLETA DE LA LLAMADA:
                ---
                {transcripcion}
                ---
                
                Proporciona un reporte estructurado y pedagógico en español con los siguientes puntos:
                1. 🏆 **Puntuación General:** (Calificación del 1 al 10).
                2. ✅ **Aciertos del Operador:** (Cosas que hizo muy bien según el procedimiento).
                3. ⚠️ **Oportunidades de Mejora:** (Errores, fallas de protocolo o tono a corregir).
                4. 📋 **Cumplimiento de Protocolo:** (¿Validó identidad? ¿Mostró empatía? ¿Aplicó correctamente el reembolso o política?).
                5. 💡 **Consejo Práctico:** (Una recomendación directa para la próxima llamada).
                """

                modelos_gratuitos = obtener_modelos_gratuitos_en_vivo()
                evaluacion_res = None

                for modelo in modelos_gratuitos:
                    try:
                        res = client.chat.completions.create(
                            model=modelo,
                            messages=[{"role": "user", "content": prompt_evaluacion}],
                        )
                        evaluacion_res = res.choices[0].message.content
                        if evaluacion_res:
                            break
                    except Exception:
                        continue

                if evaluacion_res:
                    st.session_state.evaluacion_texto = evaluacion_res
                    st.session_state.evaluado = True
                    st.rerun()
                else:
                    st.error("❌ No se pudo procesar la evaluación. Inténtalo de nuevo.")

# ---------------------------------------------------------
# MODO 2: REPORTE DE EVALUACIÓN Y NUEVA GESTIÓN
# ---------------------------------------------------------
else:
    st.markdown("---")
    st.subheader("📊 Reporte de Auditoría y Evaluación de Calidad")
    
    st.info(st.session_state.evaluacion_texto)

    st.markdown("---")
    # BOTÓN PARA REINICIAR Y NUEVA GESTIÓN
    if st.button("🔄 Iniciar Nueva Gestión", type="primary", use_container_width=True):
        st.session_state.messages = []
        st.session_state.evaluado = False
        st.session_state.evaluacion_texto = ""
        if "last_audio" in st.session_state:
            del st.session_state["last_audio"]
        st.rerun()