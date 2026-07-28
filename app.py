import streamlit as st
from openai import OpenAI
from gtts import gTTS
import io
import json
import urllib.request
import speech_recognition as sr
from audio_recorder_streamlit import audio_recorder

# Configuración de la página
st.set_page_config(
    page_title="Simulador Call Center Pro", 
    page_icon="🎙️", 
    layout="centered",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------
# INYECCIÓN DE CSS PERSONALIZADO PARA MEJORAR LA ESTÉTICA
# ---------------------------------------------------------
st.markdown("""
    <style>
    /* Estilo del fondo y contenedores */
    .stApp {
        background-color: #f4f6f9;
    }
    
    /* Encabezado principal */
    .main-header {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        padding: 24px;
        border-radius: 12px;
        color: white;
        text-align: center;
        margin-bottom: 25px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    
    .main-header h1 {
        color: white !important;
        margin: 0;
        font-size: 1.8rem;
    }
    
    .main-header p {
        color: #e0e6ed;
        margin-top: 5px;
        font-size: 0.95rem;
    }

    /* Caja del grabador de voz */
    .mic-container {
        background: white;
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        border: 1px solid #e1e8ed;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        margin-bottom: 20px;
    }

    /* Estilos para el reporte de evaluación */
    .report-card {
        background-color: #ffffff;
        border-left: 5px solid #2a5298;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        margin-top: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# Encabezado visual estilizado
st.markdown("""
    <div class="main-header">
        <h1>🎙️ Simulador de Llamadas & Auditoría</h1>
        <p>Entrenamiento interactivo por voz en tiempo real con IA</p>
    </div>
""", unsafe_allow_html=True)

# Inicializar estados
if "messages" not in st.session_state:
    st.session_state.messages = []
if "evaluado" not in st.session_state:
    st.session_state.evaluado = False
if "evaluacion_texto" not in st.session_state:
    st.session_state.evaluacion_texto = ""

def transcribir_audio(audio_bytes):
    r = sr.Recognizer()
    audio_file = io.BytesIO(audio_bytes)
    try:
        with sr.AudioFile(audio_file) as source:
            audio_data = r.record(source)
            return r.recognize_google(audio_data, language="es-ES")
    except sr.UnknownValueError:
        st.warning("⚠️ Audio no reconocido. Habla más cerca del micrófono.")
        return None
    except Exception as e:
        st.error(f"❌ Error de audio: {e}")
        return None

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

# Sidebar estilizada
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/4712/4712109.png", width=70)
    st.title("Panel de Control")
    api_key_input = st.text_input("OpenRouter API Key:", type="password")
    api_key = api_key_input.strip() if api_key_input else ""
    rol_ia = st.selectbox("Rol asignado a la IA:", ["Cliente (Usuario es Operador)", "Operador (Usuario es Cliente)"])
    
    st.markdown("---")
    st.subheader("📚 Protocolo / Guion")
    manual_context = st.text_area(
        "Instrucciones de la llamada:",
        value="El cliente llama porque no reconoce un cobro de $50 en su estado de cuenta. El operador debe pedir número de cédula, validar identidad, mostrar empatía y aplicar la política de reembolso automático si es menor a $100.",
        height=180
    )

if not api_key:
    st.info("💡 Ingresa tu OpenRouter API Key en el panel izquierdo para comenzar.")
    st.stop()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
    default_headers={
        "HTTP-Referer": "https://streamlit.io",
        "X-Title": "Simulador Call Center Pro"
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
2. Mantén tus respuestas MUY BREVES (máximo 1 a 2 oraciones sencillas).
3. No uses texto entre paréntesis ni acotaciones.
"""

# Mostrar historial
for message in st.session_state.messages:
    avatar = "👨‍💼" if message["role"] == "user" else "🎧"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# MODO 1: LLAMADA ACTIVA
if not st.session_state.evaluado:
    st.markdown('<div class="mic-container">', unsafe_allow_html=True)
    st.write("🎙️ **Control de Audio de la Llamada**")
    st.caption("Presiona el micrófono para hablar y vuelve a presionarlo al terminar la frase.")
    
    audio_bytes = audio_recorder(
        text="",
        recording_color="#e74c3c",
        neutral_color="#27ae60",
        icon_size="2x"
    )
    st.markdown('</div>', unsafe_allow_html=True)

    prompt_texto = st.chat_input("O escribe tu respuesta aquí...")
    input_usuario = None

    if audio_bytes and ("last_audio" not in st.session_state or st.session_state.last_audio != audio_bytes):
        st.session_state.last_audio = audio_bytes
        with st.spinner("🎧 Procesando voz..."):
            input_usuario = transcribir_audio(audio_bytes)

    if prompt_texto:
        input_usuario = prompt_texto

    if input_usuario:
        st.session_state.messages.append({"role": "user", "content": input_usuario})
        with st.chat_message("user", avatar="👨‍💼"):
            st.markdown(input_usuario)

        with st.chat_message("assistant", avatar="🎧"):
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

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔴 Finalizar Llamada y Auditar Gestion", type="primary", use_container_width=True):
        if len(st.session_state.messages) < 2:
            st.warning("⚠️ Realiza al menos un intercambio de voz antes de evaluar.")
        else:
            with st.spinner("📊 Analizando el cumplimiento del protocolo..."):
                transcripcion = ""
                for msg in st.session_state.messages:
                    rol = "OPERADOR" if msg["role"] == "user" else "CLIENTE"
                    transcripcion += f"{rol}: {msg['content']}\n"

                prompt_evaluacion = f"""
                Eres un Auditor de Calidad Senior de Call Center.
                Evalúa la siguiente llamada basándote estrictamente en este manual:
                
                MANUAL:
                ---
                {manual_context}
                ---
                
                TRANSCRIPCIÓN:
                ---
                {transcripcion}
                ---
                
                Proporciona un reporte en español bien estructurado con los siguientes encabezados en Markdown:
                ### 🏆 Nota Final (1 al 10)
                ### ✅ Puntos Fuertes
                ### ⚠️ Errores / Oportunidades
                ### 💡 Recomendación Práctica
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

# MODO 2: REPORTES Y RESULTADOS
else:
    st.subheader("📋 Auditoría de Calidad de la Gestión")
    
    st.markdown(f'<div class="report-card">{st.session_state.evaluacion_texto}</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 Iniciar Nueva Gestión", type="primary", use_container_width=True):
        st.session_state.messages = []
        st.session_state.evaluado = False
        st.session_state.evaluacion_texto = ""
        if "last_audio" in st.session_state:
            del st.session_state["last_audio"]
        st.rerun()