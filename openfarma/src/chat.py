import io
import os
import base64
import smtplib
import streamlit as st
import requests
from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime
from fpdf import FPDF
from PIL import Image
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from dotenv import load_dotenv

# from assistant.thread import Thread
from .params import USER_CHAT_COLUMNS, BOT_CHAT_COLUMNS
from .utils import PromptTracker

load_dotenv()

DJANGO_API_URL = os.getenv("DJANGO_API_URL")
SHARED_AUTH_TOKEN = os.getenv("SHARED_AUTH_TOKEN")


def encodeImage(image_path: str) -> str:
    image = Image.open(image_path)
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()


@dataclass
class ChatStyle:
    style: str = """
        <style>
        /* Ocultar elementos innecesarios del layout de Streamlit */
        div[data-testid="stToolbar"],
        div[data-testid="stDecoration"],
        div[data-testid="stStatusWidget"],
        #MainMenu, header, footer {
            visibility: hidden;
            height: 0;
        }

        /* Estilos de mensajes */
        .bot-message, .user-message {
            background-color: #FFFFFF;
            border-style: dotted;
            border-color: #8EA749;
            border-width: 3px;
            border-radius: 10px;
            padding: 15px;
            color: black;
            font-size: 20px;
            position: relative;
            top: -13.5px;
            margin-bottom: 10px;
        }
        .bot-message { margin-left: auto; }
        .user-message { margin-right: auto; }

        /* Contenedor principal */
        .main .block-container {
            width: 100% !important;
            max-width: 80% !important;
            min-height: 100vh !important;
            padding-top: 6rem; /* espacio para el header */
            padding-right: 1rem;
            padding-left: 1rem;
            padding-bottom: 10rem; /* espacio para el input fijo */
        }

        /* Encabezado fijo */
        .fixed-header {
            position: fixed;
            top: 0;
            width: 100%;
            background-color: #FFFFFF;
            z-index: 1000;
            padding: 10px 0;
            text-align: center;
        }
        .header-image {
            width: 12.5%;
            max-width: 100%;
        }
        .header-caption {
            margin-top: 60px;
            font-size: 24px;
        }

        /* Contenedor del chat con espacio inferior para input */
        .chat-container {
            max-height: 70vh;
            overflow-y: auto;
            margin-bottom: 120px; /* espacio para input fijo */
            padding: 10px;
        }

        /* Input fijo en la parte inferior */
        .input-section {
            position: fixed;
            bottom: 0;
            width: 100%;
            background-color: white;
            padding: 1rem 1rem 2rem 1rem;
            box-shadow: 0 -4px 10px rgba(0,0,0,0.05);
            z-index: 999;
        }

        /* Estilo para tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 10px;
            justify-content: center;
        }
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            padding: 8px 24px;
            border-radius: 8px;
            font-weight: 500;
        }
        .stTabs [aria-selected="true"] {
            background-color: var(--primary-color);
            color: black;
        }

        /* Audio input */
        .stAudioInput {
            border: 2px dashed #ddd;
            border-radius: 8px;
            padding: 15px;
            background-color: #f8f9fa;
            text-align: center;
        }

        /* Animación suave para mensajes */
        .stChatMessage {
            animation: fadeIn 0.3s ease-in;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        /* Responsive */
        @media (max-width: 768px) {
            .chat-container {
                max-height: 60vh;
            }
            .header-caption {
                font-size: 18px;
            }
        }
        </style>
    """


@dataclass
class ChatConfig:
    title: str = "💬 openfarmAI"
    header_caption: str = "Tu asistente farmacéutico virtual"
    header_logo_path: str = "path/to/header/logo"
    user_avatar_path: str = "path/to/user/avatar"
    bot_avatar_path: str = "path/to/bot/avatar"
    input_placeholder: str = "Escriba su consulta aquí..."
    loading_text: str = "Buscando información..."


class ChatbotApi:
    def __init__(
        self,
        phone: str,
        config: Optional[ChatConfig] = None,
        style: Optional[ChatStyle] = None,
    ):
        self.phone = phone
        self.config = config or ChatConfig()
        self.style = style or ChatStyle()
        self.is_processing = False
        self.prompts_queue: List[str] = []
        self.prompt_tracker = PromptTracker()
        self.messages: List[Dict[str, str]] = []

        # Initialize with welcome message
        # TODO
        # self.addMessage("Hola, ¿en qué te puedo ayudar?", "assistant")

    def _get_messages(self) -> List[Dict[str, str]]:
        """Get the current list of messages"""
        return self.messages

    def _exportToTxt(self, output_path: str, metadata: dict) -> str:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(f"Chat Export - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 50 + "\n\n")

            # Add metadata
            f.write("INFORMACIÓN\n")
            f.write("-" * 50 + "\n")
            for key, value in metadata.items():
                if value:  # Only write if value is not empty
                    f.write(f"{key}: {value}\n")
            f.write("-" * 50 + "\n\n")

            for msg in self._get_messages():
                role = "Usuario" if msg["role"] == "user" else "Asistente"
                timestamp = msg["timestamp"].strftime("%H:%M:%S")  # type: ignore
                f.write(f"[{role} - {timestamp}]\n")
                f.write(f"{msg['content']}\n")
                f.write("-" * 50 + "\n\n")

        return output_path

    def _exportToMd(self, output_path: str, metadata: dict) -> str:
        """Export conversation to a markdown file with header logo"""
        with open(output_path, "w", encoding="utf-8") as f:
            # Add header logo as base64 image
            with open(self.config.header_logo_path, "rb") as img_file:
                b64_image = base64.b64encode(img_file.read()).decode()
                f.write(
                    f'<img src="data:image/png;base64,{b64_image}" width="150px" align="left"/>\n\n'
                )

            f.write(
                f"# ChatBot - Conversación - {datetime.now().strftime('%Y-%m-%d')}\n\n"
            )

            # Add metadata
            f.write("## Información\n\n")
            for key, value in metadata.items():
                if value:  # Only write if value is not empty
                    f.write(f"- **{key}:** {value}\n")
            f.write("\n---\n\n")

            for msg in self._get_messages():
                role = "👤 Usuario" if msg["role"] == "user" else "🤖 Asistente"
                timestamp = msg["timestamp"].strftime("%H:%M:%S")  # type: ignore
                f.write(f"### {role} ({timestamp})\n\n")
                f.write(f"{msg['content']}\n\n")
                f.write("---\n\n")

        return output_path

    def _exportToPdf(self, output_path: str, metadata: dict) -> str:
        """Export conversation to a PDF file with header logo"""
        pdf = FPDF()
        pdf.add_page()

        # Add header logo
        pdf.image(
            self.config.header_logo_path, x=10, y=10, w=40
        )  # Adjust w=40 to change logo size
        pdf.ln(30)  # Space after logo

        # Configure fonts and add title
        pdf.set_font("Arial", "B", 16)
        pdf.cell(
            0,
            10,
            f"ChatBot - Conversación - {datetime.now().strftime('%Y-%m-%d')}",
            ln=True,
        )
        pdf.ln(10)

        # Add metadata
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Información:", ln=True)
        pdf.set_font("Arial", size=12)
        for key, value in metadata.items():
            if value:  # Only write if value is not empty
                pdf.cell(0, 10, f"{key}: {value}", ln=True)
        pdf.ln(10)

        # Add messages
        pdf.set_font("Arial", size=12)
        for msg in self._get_messages():
            role = "Usuario" if msg["role"] == "user" else "Asistente"
            timestamp = msg["timestamp"].strftime("%H:%M:%S")  # type: ignore

            # Role header with timestamp
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 10, f"{role} - {timestamp}:", ln=True)

            # Message content
            pdf.set_font("Arial", size=12)
            pdf.multi_cell(0, 10, msg["content"])
            pdf.ln(5)

            # Separator line
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(10)

        pdf.output(output_path)
        return output_path

    def addMessage(self, content: str, role: str) -> None:
        message = {"role": role, "content": content, "timestamp": datetime.now()}
        self.messages.append(message)
        # self.thread.addMessage(content=content, role=role)

    def addStyleToMessage(self, message: str, role: str) -> str:
        if role == "user":
            return f'<div class="chat-message user-message">{message}</div>'
        else:
            return f'<div class="chat-message bot-message">{message}</div>'

    def clearChat(self, report: bool = True) -> None:
        """
        Clear all chat messages and reset the thread.
        Adds a welcome message after clearing.
        """
        if report:
            self.prompt_tracker.reportPrompts()  # Report prompts before clearing
        self.messages = []
        # self.thread = Thread(self.thread.api_key)
        # self.addMessage("Hola, ¿en qué te puedo ayudar?", "assistant")

    def exportConversation(self, format: str, output_path: str, metadata: dict) -> str:
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"chat_export_{timestamp}.{format}"
            output_path = os.path.join(os.getcwd(), filename)

        if format.lower() == "txt":
            return self._exportToTxt(output_path, metadata)
        elif format.lower() == "md":
            return self._exportToMd(output_path, metadata)
        elif format.lower() == "pdf":
            return self._exportToPdf(output_path, metadata)
        else:
            raise ValueError("Format must be 'txt', 'md', or 'pdf'")

    def processQueue(self) -> bool:
        if self.prompts_queue:  # and not self.thread.isRunActive():
            # Pop the first prompt from the queue
            # It has already been added to the thread by the processUserInput method
            message = self.prompts_queue.pop(0)

            # Process in thread
            with st.spinner(self.config.loading_text):
                # self.thread.runWithStreaming(self.assistant_id, handlers)
                response = requests.post(
                    f"{DJANGO_API_URL}/conversations/reply/",
                    headers={"Authorization": f"Bearer {SHARED_AUTH_TOKEN}"},
                    json={"phone": self.phone, "message": message},
                )
                response = response.json()

            # Get and add assistant response
            # response = self.thread.retrieveLastMessage()
            # content = response["content"][0].text.value
            self.addMessage(response["reply"], "assistant")

            # Update processing status
            self.is_processing = bool(self.prompts_queue)

            # Increment prompt counter
            self.prompt_tracker.incrementPromptCount()

            return True
        return False

    def processUserInput(self, user_input: str) -> None:
        """
        Process user input and add it to the processing queue.

        Args:
            user_input (str): User's message text
        """
        if user_input:
            # Add user message immediately and rerun to show it
            self.addMessage(user_input, "user")
            self.prompts_queue.append(user_input)
            self.is_processing = True

    def renderChatInterface(self) -> bool:
        # Header
        header_logo = encodeImage(self.config.header_logo_path)
        st.markdown(
            f"""
            <div class="fixed-header">
                <div class="header-content">
                    <img src="data:image/jpeg;base64,{header_logo}" class="header-image">
                </div>
            </div>
        """,
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""<div class="header-caption">{self.config.header_caption}</div>""",
            unsafe_allow_html=True,
        )

        # Chat container - display messages
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        chat_container = st.container()
        self.displayMessages(chat_container)
        st.markdown("</div>", unsafe_allow_html=True)

        # Input section - organized in a better layout
        st.markdown('<div class="input-section">', unsafe_allow_html=True)

        # Create tabs or columns for better organization
        input_tab1, input_tab2 = st.tabs(["💬 Texto", "🎤 Audio"])

        with input_tab1:
            # Text input
            user_input = st.chat_input(
                placeholder=self.config.input_placeholder,
                disabled=self.is_processing,
                key="chat_input",
            )

            if user_input:
                self.processUserInput(user_input)

        with input_tab2:
            # Audio input section
            audio_file = st.audio_input(
                label="Grabar mensaje de voz",
                key="audio_input",
                disabled=self.is_processing,
                help="Graba tu mensaje y presiona 'Enviar audio' para enviarlo",
            )

            if audio_file is not None:
                if st.button(
                    "🎵 Enviar audio", disabled=self.is_processing, type="primary"
                ):
                    return self._process_audio_input(audio_file)

        st.markdown("</div>", unsafe_allow_html=True)
        return False

    def _process_audio_input(self, audio_file) -> bool:
        """Método auxiliar para procesar el input de audio"""
        self.is_processing = True

        try:
            files = {"audio": (audio_file.name, audio_file, "audio/wav")}
            data = {"phone": self.phone}
            headers = {"Authorization": f"Bearer {os.getenv('SHARED_AUTH_TOKEN')}"}

            with st.spinner(self.config.loading_text):
                response = requests.post(
                    f"{DJANGO_API_URL}/conversations/reply/",
                    data=data,
                    files=files,
                    headers=headers,
                )
                response = response.json()

            # Add messages to chat
            self.addMessage(f"🎤 Audio enviado: {response['message']}", "user")
            reply = response["reply"]
            self.addMessage(reply, "assistant")

            self.prompt_tracker.incrementPromptCount()
            st.success("✅ Audio procesado correctamente")

            return True

        except Exception as e:
            st.error(f"❌ Error al procesar el audio: {str(e)}")
            return False

        finally:
            self.is_processing = False

    def displayMessages(self, chat_container) -> None:
        """Display all messages in the Streamlit container with improved spacing"""
        with chat_container:
            for i, msg in enumerate(self._get_messages()):
                # Add some spacing between messages
                if i > 0:
                    st.markdown("<br>", unsafe_allow_html=True)

                if msg["role"] == "user":
                    _, right = st.columns(USER_CHAT_COLUMNS)
                    with right:
                        with st.chat_message(
                            msg["role"], avatar=self.config.user_avatar_path
                        ):
                            message = self.addStyleToMessage(
                                msg["content"], msg["role"]
                            )
                            st.write(message, unsafe_allow_html=True)
                else:
                    left, _ = st.columns(BOT_CHAT_COLUMNS)
                    with left:
                        with st.chat_message(
                            msg["role"], avatar=self.config.bot_avatar_path
                        ):
                            message = self.addStyleToMessage(
                                msg["content"], msg["role"]
                            )
                            st.write(message, unsafe_allow_html=True)

    def sendConversationEmail(
        self,
        from_email: str,
        to_email: str,
        password: str,
        attachments: List[str],
        metadata: dict,
    ):
        try:
            # Email settings
            message = MIMEMultipart()
            message["From"] = from_email
            message["To"] = to_email
            message["Subject"] = (
                f"Dev:Reporte de Conversación OpenFarma - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            )

            # Create email body
            body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6;">
                <h2 style="color: #2c3e50;">Reporte de Conversación - OpenFarma AI</h2>
                
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px;">
                    <h3 style="color: #2c3e50;">Información General:</h3>
                    <ul style="list-style-type: none; padding-left: 0;">
                        <li><strong>Fecha:</strong> {datetime.now().strftime("%d/%m/%Y")}</li>
                        <li><strong>Hora:</strong> {datetime.now().strftime("%H:%M:%S")}</li>
                        <li><strong>Usuario:</strong> {metadata.get("Usuario", "No especificado")}</li>
                        <li><strong>Sucursal:</strong> {metadata.get("Sucursal", "No especificada")}</li>
                        <li><strong>Dirección:</strong> {metadata.get("Dirección", "No especificada")}</li>
                        <li><strong>Localidad:</strong> {metadata.get("Localidad", "No especificada")}</li>
                    </ul>
                </div>

                <div style="margin-top: 20px;">
                    <h3 style="color: #2c3e50;">Detalles de la Conversación:</h3>
                    <ul>
                        <li>Cantidad de mensajes intercambiados: {len(self._get_messages())}</li>
                        <li>Duración de la conversación: {self._computeChatElapsedTime()}</li>
                        <li>Archivos adjuntos: {len(attachments)} documento(s)</li>
                    </ul>
                </div>

                <p style="color: #666; font-style: italic;">
                    Nota: Por razones de privacidad y seguridad, el contenido detallado 
                    de la conversación se encuentra en los archivos adjuntos.
                </p>

                <hr style="border: 1px solid #eee; margin: 20px 0;">
                
                <footer style="color: #666; font-size: 12px;">
                    <p>Este es un mensaje automático generado por OpenFarma AI Assistant.</p>
                    <p>Por favor no responda a este correo.</p>
                    <p style="color: #ff0000;">Esta conversación fue enviada desde la versión beta del software.</p>
                </footer>
            </body>
            </html>
            """

            # Attach body
            message.attach(MIMEText(body, "html"))

            # Attach files
            for file_path in attachments:
                try:
                    with open(file_path, "rb") as f:
                        part = MIMEApplication(f.read(), _subtype="pdf")
                        part.add_header(
                            "Content-Disposition",
                            "attachment",
                            filename=os.path.basename(file_path),
                        )
                        message.attach(part)
                except Exception as e:
                    raise Exception(f"Error attaching file {file_path}: {str(e)}")

            # Start SMTP session
            session = smtplib.SMTP("smtp.gmail.com", 587)
            session.starttls()
            session.login(from_email, password)

            # Send email
            text = message.as_string()
            session.sendmail(from_email, to_email, text)
            session.quit()

        except smtplib.SMTPAuthenticationError:
            raise Exception("Authentication error. Check email address and password.")
        except smtplib.SMTPConnectError:
            raise Exception(
                "Failed to connect to SMTP server. Check internet connection."
            )
        except Exception as e:
            raise Exception(f"Error sending email: {str(e)}")

    def _computeChatElapsedTime(self) -> str:
        if len(self._get_messages()) < 2:
            return "Menos de 1 minuto"

        start_time = self._get_messages()[0]["timestamp"]
        end_time = self._get_messages()[-1]["timestamp"]
        duration = end_time - start_time  # type: ignore

        minutes = duration.total_seconds() / 60
        if minutes < 1:
            return "Menos de 1 minuto"
        elif minutes < 60:
            return f"{int(minutes)} minutos"
        else:
            hours = minutes / 60
            return f"{int(hours)} horas {int(minutes % 60)} minutos"
