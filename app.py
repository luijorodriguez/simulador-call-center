import streamlit as st
import google.genai as genai

# Configuración de la página
st.set_page_config(page_title="Simulador de Call Center", page_icon="📞", layout="centered")

st.title("📞 Simulador de Llamadas de Entrenamiento")
st.caption("Entorno de práctica interactivo impulsado por IA")

# Sidebar - Configuración y Base de Conocimiento
with st.sidebar:
    st.header("⚙️ Configuración del Simulador")
    api_key = st.text_input("Google Gemini API Key:", type="password")
    
    rol_ia = st.selectbox("Rol de la IA:", ["Cliente (Usuario es Operador)", "Operador (Usuario es Cliente)"])
    
    st.markdown("---")
    st.subheader("📚 Base de Conocimiento / Manual")
    manual_context = st.text_area(
        "Ingresa las políticas, guion o procedimientos del call center:",
        value="El cliente llama porque no reconoce un cobro de $50 en su estado de cuenta. El operador debe pedir número de cédula, validar identidad, mostrar empatía y aplicar la política de reembolso automático si es menor a $100.",
        height=200
    )

# Inicializar historial de chat
if "messages" not in st.session_state:
    st.session_state.messages = []

# Validar API Key
if not api_key:
    st.info("💡 Por favor, ingresa tu API Key de Gemini en el panel izquierdo para iniciar la simulación. (Es gratuita en aistudio.google.com)")
    st.stop()

# Definir el Prompt del Sistema según el rol seleccionado
prompt_sistema = f"""
Eres un participante en un simulador de entrenamiento para un call center.
Tu rol actual es: {rol_ia}.
Debes seguir strictly las siguientes políticas y contexto de la empresa:
---
{manual_context}
---
Instrucciones:
1. Actúa de forma hiperrealista como se te indicó en tu rol (con tono adecuado, objeciones o cortesía profesional).
2. Tus respuestas deben ser breves (máximo 2 a 3 oraciones), imitando la fluidez de una conversación telefónica real.
3. Mantén la simulación activa hasta que el usuario decida colgar.
"""

client = genai.Client(api_key=api_key)

# Mostrar historial de la llamada
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Entrada de texto/voz del usuario
if prompt := st.chat_input("Escribe o responde la llamada aquí..."):
    # Guardar mensaje del usuario
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generar respuesta de la IA
    with st.chat_message("assistant"):
        historial_prompt = [f"{m['role']}: {m['content']}" for m in st.session_state.messages]
        prompt_completo = f"{prompt_sistema}\n\nHistorial de la llamada:\n" + "\n".join(historial_prompt)
        
response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=prompt_completo
        )
        
        respuesta_ia = response.text
        st.markdown(respuesta_ia)
        
    # Guardar respuesta de la IA
    st.session_state.messages.append({"role": "assistant", "content": respuesta_ia})

# Botón para colgar y reiniciar
if st.button("🔴 Finalizar y Evaluar Llamada"):
    st.success("Llamada finalizada. Procesando evaluación de desempeño...")
    st.session_state.messages = []