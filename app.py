import streamlit as st
from openai import OpenAI
from gtts import gTTS
import io
import json
import random
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
# BANCO DE 30 CASOS DE ENTRENAMIENTO PARA CALL CENTER
# ---------------------------------------------------------
CASOS_DATABASE = [
    {
        "id": 1,
        "categoria": "Facturación",
        "titulo": "Cobro no reconocido de $50",
        "contexto": "El cliente llama porque ve un cobro no reconocido de $50 en su tarjeta de crédito. El operador debe solicitar cédula, validar identidad, mostrar empatía y aplicar el protocolo de reversión si es menor a $100."
    },
    {
        "id": 2,
        "categoria": "Soporte Técnico",
        "titulo": "Falla intermitente en servicio de Internet",
        "contexto": "El cliente lleva 3 días con Internet lento e intermitente. El operador debe validar datos del titular, guiar en el reinicio del módem (físico), verificar el estado de la red en zona y agendar visita técnica si no se soluciona."
    },
    {
        "id": 3,
        "categoria": "Retención y Cancelaciones",
        "titulo": "Solicitud de cancelación por aumento de tarifa",
        "contexto": "El cliente llama muy molesto exigiendo cancelar su plan mensual porque le subieron la tarifa. El operador debe mantener la calma, escuchar activamente, validar identidad y ofrecer un descuento de fidelización del 20% durante 6 meses antes de proceder con la baja."
    },
    {
        "id": 4,
        "categoria": "Facturación",
        "titulo": "Doble débito en cuenta bancaria",
        "contexto": "El cliente afirma que le descontaron dos veces la mensualidad de este mes. El operador debe solicitar la fecha exacta de las transacciones, pedir la cédula, revisar el sistema de cobros y generar la orden de devolución en 24-48 horas hábiles."
    },
    {
        "id": 5,
        "categoria": "Servicio al Cliente",
        "titulo": "Producto o pedido retrasado",
        "contexto": "El cliente compró un equipo online que debía llegar hace 2 días y no ha recibido actualizaciones. El operador debe pedir el número de pedido o cédula, rastrear la guía en el sistema logístico, dar estatus claro y brindar disculpa corporativa ofreciendo un bono de envío gratis futuro."
    },
    {
        "id": 6,
        "categoria": "Seguridad",
        "titulo": "Bloqueo de clave de banca en línea / app",
        "contexto": "El usuario bloqueó su usuario por introducir mal la clave tres veces. El operador debe hacer 3 preguntas estrictas de seguridad (cédula, fecha de nacimiento, últimos 4 dígitos de cuenta/tarjeta) para proceder al desbloqueo y envío de clave temporal."
    },
    {
        "id": 7,
        "categoria": "Facturación",
        "titulo": "Cobro excesivo en servicio Roaming Internacional",
        "contexto": "El cliente viajó al exterior y recibió una factura de $300 por consumo de datos involuntario. El operador debe explicar amablemente el consumo según registro del sistema, pero ofrecer un ajuste especial a plan viajero reducido si no fue informado previamente."
    },
    {
        "id": 8,
        "categoria": "Soporte Técnico",
        "titulo": "Línea móvil sin señal / SIM Inactiva",
        "contexto": "El cliente compró un chip nuevo pero su teléfono dice 'Sin Servicio'. El operador debe confirmar número de Cédula e ICCID del chip, verificar si la línea está activa en plataforma y guiar al usuario para configurar el APN de la red."
    },
    {
        "id": 9,
        "categoria": "Seguridad / Reclamos",
        "titulo": "Reporte de extravío o robo de tarjeta",
        "contexto": "El cliente llama alarmado porque perdió su billetera con sus tarjetas. El operador debe priorizar la llamada, pedir número de cédula de inmediato, realizar la suspensión definitiva de los plásticos y emitir la orden de reposición."
    },
    {
        "id": 10,
        "categoria": "Servicio al Cliente",
        "titulo": "Cambio de dirección de entrega de pedido en tránsito",
        "contexto": "El usuario se mudó repentinamente y requiere cambiar la dirección de un envío que sale hoy. El operador debe validar titularidad del pedido, verificar si la guía ya fue recolectada por la agencia y gestionar la modificación en el sistema antes del reparto."
    },
    {
        "id": 11,
        "categoria": "Ventas y Upgrades",
        "titulo": "Solicitud de reducción de plan (Downgrade)",
        "contexto": "El cliente quiere bajarse al plan más económico porque recortó sus gastos personales. El operador debe evaluar su consumo actual, explicar los beneficios que perdería de forma empática y ofrecer un paquete ajustado a sus necesidades."
    },
    {
        "id": 12,
        "categoria": "Soporte Técnico",
        "titulo": "Decodificador de TV sin señal (pantalla negra/roja)",
        "contexto": "El usuario no puede ver televisión y le aparece error de señal en pantalla. El operador debe guiarlo paso a paso para verificar las conexiones de cable coaxial/HDMI y realizar un reenvío de señal (refresh) desde la consola."
    },
    {
        "id": 13,
        "categoria": "Facturación",
        "titulo": "Aplicación de código de descuento no reflejado",
        "contexto": "El cliente realizó una compra ingresando un cupón de 15% de descuento, pero la factura llegó por el precio completo. El operador debe pedir el código del cupón, validar la vigencia de la promoción y emitir una nota de crédito por el excedente."
    },
    {
        "id": 14,
        "categoria": "Servicio al Cliente",
        "titulo": "Reclamo por mala atención en sucursal presencial",
        "contexto": "El cliente está sumamente molesto por el trato que recibió en una tienda física hace unas horas. El operador debe aplicar escucha activa, ofrecer disculpas a nombre de la empresa, tomar el reporte de queja detallado y remitirlo a gestión humana."
    },
    {
        "id": 15,
        "categoria": "Cobranzas",
        "titulo": "Solicitud de prórroga o convenio de pago por mora",
        "contexto": "El cliente tiene 2 meses de mora por desempleo y teme el corte definitivo del servicio. El operador debe validar sus datos, verificar antigüedad como cliente y ofrecer un convenio de pago diferido en 3 cuotas sin intereses."
    },
    {
        "id": 16,
        "categoria": "Garantías",
        "titulo": "Producto entregado defectuoso / averiado",
        "contexto": "El cliente recibió un electrodoméstico que no enciende. El operador debe solicitar cédula, número de factura, tomar reporte del estado del empaque y generar la guía de recolección gratuita para revisión técnica o reemplazo."
    },
    {
        "id": 17,
        "categoria": "Servicio al Cliente",
        "titulo": "Actualización de datos personales y correo electrónico",
        "contexto": "El cliente cambió de correo y número telefónico y no recibe sus facturas digitales. El operador debe efectuar la validación estricta de seguridad previa antes de modificar el correo electrónico de contacto en la base de datos."
    },
    {
        "id": 18,
        "categoria": "Facturación",
        "titulo": "Cargo por mora indebido cobrado al cliente",
        "contexto": "Al cliente le cobraron recargo por pago tardío, pero él pagó antes de la fecha límite por transferencia. El operador debe solicitar el número de referencia del comprobante de pago, verificar en sistema y anular el recargo indebido."
    },
    {
        "id": 19,
        "categoria": "Retención y Cancelaciones",
        "titulo": "Cancelación por mudanza a zona sin cobertura",
        "contexto": "El cliente debe dar de baja su servicio de fibra óptica porque se traslada a un sector rural sin cobertura. El operador debe confirmar la falta de cobertura en mapa, explicar los trámites de devolución de equipos y no cobrar penalidad por causa justificada."
    },
    {
        "id": 20,
        "categoria": "Soporte Técnico",
        "titulo": "Falla al intentar realizar pagos por la app móvil",
        "contexto": "La app del cliente se cierra o arroja 'Error 500' cada vez que intenta pagar la factura. El operador debe tomar captura/detalle del error, recomendar borrar caché de la app y elevar la incidencia al departamento de TI."
    },
    {
        "id": 21,
        "categoria": "Servicio al Cliente",
        "titulo": "Consulta de estatus de trámite o reclamo anterior",
        "contexto": "El cliente llama para conocer el avance de un caso ingresado hace 5 días hábiles. El operador debe solicitar el número de ticket o cédula, consultar el sistema de tickets CRM y comunicarle el estatus exacto y tiempos restantes."
    },
    {
        "id": 22,
        "categoria": "Fidelización",
        "titulo": "Consulta y canje de puntos del programa de lealtad",
        "contexto": "El cliente quiere saber cuántos puntos acumulados tiene y cómo cambiarlos por saldo o productos. El operador debe revisar la cuenta, informarle el saldo disponible y guiarlo en el procedimiento de canje inmediato."
    },
    {
        "id": 23,
        "categoria": "Facturación",
        "titulo": "Inconformidad con cobro de suscripción no autorizada",
        "contexto": "Aparece un seguro asistencial adicional de $5/mes que el cliente afirma nunca haber contratado. El operador debe pedir cédula, dar de baja inmediata al servicio adicional y tramitar el reembolso de las cuotas cobradas."
    },
    {
        "id": 24,
        "categoria": "Servicio al Cliente",
        "titulo": "Solicitud de reagendamiento de visita técnica",
        "contexto": "El técnico iba a ir hoy pero el usuario tuvo una emergencia y no estará en casa. El operador debe verificar la agenda disponible en el sistema y programar la visita en un rango horario conveniente para el cliente."
    },
    {
        "id": 25,
        "categoria": "Soporte Técnico",
        "titulo": "Problemas de sincronización o emparejamiento",
        "contexto": "El usuario no logra conectar su nuevo smartwatch o equipo inteligente con la plataforma. El operador debe mantener la paciencia y guiar paso a paso el reinicio de Bluetooth y emparejamiento desde los ajustes."
    },
    {
        "id": 26,
        "categoria": "Cobranzas",
        "titulo": "Confirmación de recepción de pago no reflejado en sistema",
        "contexto": "El usuario pagó hace 24 horas pero le sigue apareciendo el servicio suspendido por falta de pago. El operador debe pedir el número de depósito o transferencia, validar la conciliación manual y habilitar el reconexión de emergencia."
    },
    {
        "id": 27,
        "categoria": "Servicio al Cliente",
        "titulo": "Solicitud de envío de factura detallada en PDF",
        "contexto": "El cliente requiere la factura desglosada del mes pasado para trámites de impuestos en su empresa. El operador debe confirmar cédula/RIF y correo destino para hacer el reenvío automático del PDF corporativo."
    },
    {
        "id": 28,
        "categoria": "Ventas",
        "titulo": "Información y requisitos para contratación de nuevo servicio",
        "contexto": "Un usuario interesado llama para averiguar qué requisitos necesita para contratar una línea corporativa. El operador debe brindar la información de tarifas de forma clara, solicitar datos de contacto y generar un prospecto de venta."
    },
    {
        "id": 29,
        "categoria": "Seguridad",
        "titulo": "Notificación de intento de suplantación / Phishing",
        "contexto": "El cliente recibió un SMS pidiendo sus claves a nombre de la empresa y quiere verificar si fue real. El operador debe calmar al cliente, confirmar que la empresa nunca pide claves, registrar el número emisor para el equipo de ciberseguridad."
    },
    {
        "id": 30,
        "categoria": "Retención y Cancelaciones",
        "titulo": "Cliente insatisfecho con la velocidad contratada vs real",
        "contexto": "El cliente contratÓ 300 Mbps pero dice que los test de velocidad solo le marcan 50 Mbps por WiFi. El operador debe explicar empáticamente la diferencia entre prueba por cable vs WiFi, realizar pruebas de canal y ofrecer soporte técnico avanzado antes de considerar baja."
    }
]

# ---------------------------------------------------------
# ESTILOS CSS
# ---------------------------------------------------------
st.markdown("""
    <style>
    .stApp { background-color: #f4f6f9; }
    .main-header {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        padding: 20px;
        border-radius: 12px;
        color: white;
        text-align: center;
        margin-bottom: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    .main-header h1 { color: white !important; margin: 0; font-size: 1.8rem; }
    .agent-bar {
        background: white;
        padding: 12px 20px;
        border-radius: 8px;
        border-left: 5px solid #2a5298;
        margin-bottom: 15px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.05);
    }
    .case-card {
        background: #eef2f7;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #d0d7de;
        margin-bottom: 15px;
    }
    .mic-container {
        background: white;
        padding: 18px;
        border-radius: 12px;
        text-align: center;
        border: 1px solid #e1e8ed;
        margin-bottom: 15px;
    }
    .report-card {
        background-color: #ffffff;
        border-left: 5px solid #28a745;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    </style>
""", unsafe_allow_html=True)

# Inicializar estados de la sesión
if "agente_nombre" not in st.session_state:
    st.session_state.agente_nombre = ""
if "agente_cedula" not in st.session_state:
    st.session_state.agente_cedula = ""
if "registrado" not in st.session_state:
    st.session_state.registrado = False
if "messages" not in st.session_state:
    st.session_state.messages = []
if "evaluado" not in st.session_state:
    st.session_state.evaluado = False
if "evaluacion_texto" not in st.session_state:
    st.session_state.evaluacion_texto = ""
if "casos_usados" not in st.session_state:
    st.session_state.casos_usados = []
if "caso_actual" not in st.session_state:
    st.session_state.caso_actual = None

# Funciones auxiliares
def seleccionar_nuevo_caso():
    casos_disponibles = [c for c in CASOS_DATABASE if c["id"] not in st.session_state.casos_usados]
    if not casos_disponibles:
        st.session_state.casos_usados = []  # Reiniciar si completó los 30 casos
        casos_disponibles = CASOS_DATABASE
    
    caso = random.choice(casos_disponibles)
    st.session_state.casos_usados.append(caso["id"])
    st.session_state.caso_actual = caso

def transcribir_audio(audio_bytes):
    r = sr.Recognizer()
    audio_file = io.BytesIO(audio_bytes)
    try:
        with sr.AudioFile(audio_file) as source:
            audio_data = r.record(source)
            return r.recognize_google(audio_data, language="es-ES")
    except sr.UnknownValueError:
        st.warning("⚠️ Audio no reconocido. Intenta hablar más claro.")
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

# Encabezado
st.markdown("""
    <div class="main-header">
        <h1>🎙️ Simulador de Call Center & Auditoría de Calidad</h1>
        <p>Sistema de Entrenamiento Interactivo por Voz</p>
    </div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# DETECCIÓN INTELIGENTE DE API KEY
# ---------------------------------------------------------
api_key = ""
if "OPENROUTER_API_KEY" in st.secrets and st.secrets["OPENROUTER_API_KEY"]:
    api_key = st.secrets["OPENROUTER_API_KEY"]
else:
    with st.sidebar:
        api_key_input = st.text_input("OpenRouter API Key:", type="password")
        api_key = api_key_input.strip() if api_key_input else ""

if not api_key:
    st.info("💡 Por favor, ingresa tu API Key para comenzar la simulación.")
    st.stop()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
    default_headers={"HTTP-Referer": "https://streamlit.io", "X-Title": "Simulador Call Center"}
)

# ---------------------------------------------------------
# ETAPA 1: REGISTRO DEL AGENTE
# ---------------------------------------------------------
if not st.session_state.registrado:
    st.subheader("👤 Registro del Agente para la Sesión")
    with st.form("form_registro"):
        nombre = st.text_input("Nombre y Apellido del Agente:")
        cedula = st.text_input("Número de Cédula / Identificación:")
        btn_ingresar = st.form_submit_button("🚀 Iniciar Sesión de Práctica", type="primary", use_container_width=True)
        
        if btn_ingresar:
            if nombre.strip() and cedula.strip():
                st.session_state.agente_nombre = nombre.strip()
                st.session_state.agente_cedula = cedula.strip()
                st.session_state.registrado = True
                seleccionar_nuevo_caso()
                st.rerun()
            else:
                st.warning("⚠️ Debes completar tanto el Nombre como la Cédula para continuar.")

# ---------------------------------------------------------
# ETAPA 2: LLAMADA Y SIMULACIÓN EN CURSO
# ---------------------------------------------------------
else:
    # Barra de información del Agente
    st.markdown(f"""
        <div class="agent-bar">
            <strong>👤 Agente:</strong> {st.session_state.agente_nombre} &nbsp;|&nbsp; 
            <strong>🪪 Cédula:</strong> {st.session_state.agente_cedula} &nbsp;|&nbsp;
            <strong>📊 Casos Realizados:</strong> {len(st.session_state.casos_usados)} / 30
        </div>
    """, unsafe_allow_html=True)

    # Detalle del Caso Asignado al Azar
    caso = st.session_state.caso_actual
    st.markdown(f"""
        <div class="case-card">
            <span style="background-color:#2a5298; color:white; padding:3px 8px; border-radius:4px; font-size:0.8rem;">
                Caso #{caso['id']} - {caso['categoria']}
            </span>
            <h4 style="margin: 8px 0 4px 0;">📋 {caso['titulo']}</h4>
            <p style="margin:0; font-size:0.92rem; color:#444;"><strong>Instrucción / Situación:</strong> {caso['contexto']}</p>
        </div>
    """, unsafe_allow_html=True)

    # Sidebar - Botón para reiniciar
    with st.sidebar:
        st.subheader("⚙️ Opciones de Sesión")
        if st.button("🚪 Cambiar de Agente", use_container_width=True):
            st.session_state.registrado = False
            st.session_state.agente_nombre = ""
            st.session_state.agente_cedula = ""
            st.session_state.messages = []
            st.session_state.evaluado = False
            st.session_state.casos_usados = []
            st.rerun()

    prompt_sistema = f"""
    Eres un cliente real que llama por teléfono a un call center de atención al cliente.
    Tu situación y motivo de llamada es estrictamente el siguiente:
    ---
    {caso['contexto']}
    ---
    Instrucciones de actuación:
    1. Actúa como un cliente real (puedes estar preocupado, confundido o molesto según el caso).
    2. Mantén respuestas MUY BREVES (máximo 1 a 2 oraciones sencillas) para simular una llamada fluida.
    3. No uses acotaciones ni texto entre paréntesis como (suspirando) o [enojado].
    """

    # Mostrar Historial de Chat
    for message in st.session_state.messages:
        avatar = "👨‍💼" if message["role"] == "user" else "🎧"
        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])

    # SI AÚN NO SE HA AUDITADO LA LLAMADA
    if not st.session_state.evaluado:
        st.markdown('<div class="mic-container">', unsafe_allow_html=True)
        st.write("🎙️ **Control de Audio (Tu Voz)**")
        st.caption("Toca el micrófono para hablar y vuelve a tocarlo para detenerte:")
        
        audio_bytes = audio_recorder(
            text="",
            recording_color="#e74c3c",
            neutral_color="#27ae60",
            icon_size="2x"
        )
        st.markdown('</div>', unsafe_allow_html=True)

        prompt_texto = st.chat_input("O escribe tu mensaje aquí...")
        input_usuario = None

        if audio_bytes and ("last_audio" not in st.session_state or st.session_state.last_audio != audio_bytes):
            st.session_state.last_audio = audio_bytes
            with st.spinner("🎧 Transcribiendo audio..."):
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
        if st.button("🔴 Finalizar Llamada y Auditar Gestión", type="primary", use_container_width=True):
            if len(st.session_state.messages) < 2:
                st.warning("⚠️ Realiza al menos un intercambio de voz antes de solicitar la auditoría.")
            else:
                with st.spinner("📊 Generando reporte de auditoría personalizado..."):
                    transcripcion = ""
                    for msg in st.session_state.messages:
                        rol = "OPERADOR" if msg["role"] == "user" else "CLIENTE"
                        transcripcion += f"{rol}: {msg['content']}\n"

                    prompt_evaluacion = f"""
                    Eres un Auditor de Calidad Senior de Call Center.
                    Evalúa la gestión del siguiente operador durante la llamada:

                    INFORMACIÓN DEL AGENTE:
                    - Nombre del Agente: {st.session_state.agente_nombre}
                    - Cédula de Identidad: {st.session_state.agente_cedula}

                    CASO EVALUADO:
                    - Caso #{caso['id']}: {caso['titulo']} ({caso['categoria']})
                    - Protocolo/Manual: {caso['contexto']}

                    TRANSCRIPCIÓN COMPLETA DE LA LLAMADA:
                    ---
                    {transcripcion}
                    ---

                    Genera un informe pedagógico en español estructurado con el siguiente formato Markdown:
                    
                    ## 📊 REPORTE DE AUDITORÍA DE CALIDAD
                    **Agente:** {st.session_state.agente_nombre} | **Cédula:** {st.session_state.agente_cedula}  
                    **Caso Evaluado:** #{caso['id']} - {caso['titulo']}

                    ---
                    ### 🏆 Nota Final: X / 10
                    ### ✅ Aciertos del Operador
                    ### ⚠️ Oportunidades de Mejora
                    ### 📋 Cumplimiento de Protocolo
                    ### 💡 Consejo Práctico para la Próxima Gestión
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

    # MODO MOSTRAR EVALUACIÓN Y SIGUIENTE CASO
    else:
        st.subheader("📋 Auditoría de Calidad Personalizada")
        st.markdown(f'<div class="report-card">{st.session_state.evaluacion_texto}</div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Iniciar Siguiente Caso (Aleatorio)", type="primary", use_container_width=True):
            st.session_state.messages = []
            st.session_state.evaluado = False
            st.session_state.evaluacion_texto = ""
            if "last_audio" in st.session_state:
                del st.session_state["last_audio"]
            seleccionar_nuevo_caso()
            st.rerun()