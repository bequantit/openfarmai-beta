import io
import os
import time
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

from assistant.thread import Thread
from .params import USER_CHAT_COLUMNS, BOT_CHAT_COLUMNS
from .utils import PromptTracker

DJANGO_API_URL = "http://127.0.0.1:8000"


def encodeImage(image_path: str) -> str:
    """Encode image to base64"""
    image = Image.open(image_path)
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()


@dataclass
class ChatStyle:
    """
    Manages CSS styling for the chat interface.

    Attributes:
        style (str): CSS styling rules for the chat interface including:
            - Message containers styling
            - Bot and user message specific styles
            - Header and layout configurations
            - Font sizes and spacing
    """

    style: str = """
        <style>
        div[data-testid="stChatMessage"] {
            background-color: white;
            margin-bottom: -25px; /* Ajusta este valor para más o menos espacio */
        }
        div[data-testid="stToolbar"] {visibility: hidden; height: 0%; position: fixed;}
        div[data-testid="stDecoration"] {visibility: hidden; height: 0%; position: fixed;}
        div[data-testid="stStatusWidget"] {visibility: hidden; height: 0%; position: fixed;}
        #MainMenu {visibility: hidden; height: 0%;}
        header {visibility: hidden; height: 0%;}
        footer {visibility: hidden; height: 0%;}
        
        /* Estilo específico para los mensajes del bot */
        .bot-message {
            background-color: #FFFFFF;
            border-style: dotted;
            border-color: #8EA749;
            border-width: 3px;
            border-radius: 10px;
            padding: 15px;
            color: black;
            font-size: 20px;  /* Ajusta el tamaño de la fuente */
            margin-left: auto;  /* Alinea los mensajes del bot a la derecha */
            position: relative;
            top: -13.5px;  /* Ajusta la posición vertical de los mensajes del usuario */
        }

        /* Estilo específico para los mensajes del usuario */
        .user-message {
            background-color: #FFFFFF;
            border-style: dotted;
            border-color: #8EA749;
            border-width: 3px;
            border-radius: 10px;
            padding: 15px;
            color: black;
            font-size: 20px;
            margin-right: auto;  /* Alinea los mensajes del usuario a la izquierda */
            position: relative;
            top: -13.5px;  /* Ajusta la posición vertical de los mensajes del usuario */
        }

        .main .block-container {
            width: 100% !important;
            max-width: 80% !important;
            padding-top: 2rem;
            padding-right: 1rem;
            padding-left: 1rem;
            padding-bottom: 2rem;
        }
        
        .chat-container {
            margin-top: 40px; /* Espacio para el header fijo */
        }
        
        .fixed-header {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            z-index: 1000;
            background-color: #FFFFFF;
            padding: 10px 0;
        }
        .header-content {
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-align: center;
            width: 100%;
        }
        .header-image {
            width: 12.5%; /* Ajusta el ancho de la imagen */
            max-width: 100%;
        }
        .header-caption {
            display: flex;
            justify-content: center;
            text-align: center;
            width: 70%;
            margin: 60px auto 0 auto;
            font-size: 24px;
        }
        div[data-testid="stChatInput"] textarea {
            font-size: 20px;  /* Ajusta el tamaño de la fuente aquí */
        }
        </style>
    """


@dataclass
class ChatConfig:
    """
    Configuration settings for the chat interface.

    Attributes:
        title (str): Chat window title
        header_caption (str): Caption displayed in the header
        header_logo_path (str): Path to the header logo image
        user_avatar_path (str): Path to the user avatar image
        bot_avatar_path (str): Path to the bot avatar image
        input_placeholder (str): Placeholder text for the chat input
        loading_text (str): Text displayed during message processing
    """

    title: str = "💬 openfarmAI"
    header_caption: str = "Tu asistente farmacéutico virtual"
    header_logo_path: str = "path/to/header/logo"
    user_avatar_path: str = "path/to/user/avatar"
    bot_avatar_path: str = "path/to/bot/avatar"
    input_placeholder: str = "Escriba su consulta aquí..."
    loading_text: str = "Buscando información..."


class ChatbotApi:
    """
    Main chat interface handler for the OpenFarma AI Assistant.

    This class manages the chat interface, message processing, and conversation export
    functionality. It integrates with OpenAI's API through a Thread class for AI responses.

    Attributes:
        config (ChatConfig): Configuration settings for the chat
        style (ChatStyle): Style settings for the chat interface
        messages (List[Dict[str, str]]): List of chat messages
        thread (Thread): OpenAI thread handler
        assistant_id (str): OpenAI assistant ID
        is_processing (bool): Flag indicating if a message is being processed
        prompts_queue (List[str]): Queue of user prompts to process
        prompt_tracker (PromptTracker): Prompt tracker for message tracking

    Example:
        ```python
        config = ChatConfig(
            title="OpenFarma AI",
            header_logo_path="path/to/logo.png",
            user_avatar_path="path/to/user.png",
            bot_avatar_path="path/to/bot.png"
        )

        chat = Chat(
            api_key="your-openai-api-key",
            assistant_id="your-assistant-id",
            config=config
        )

        # Render the chat interface
        chat.renderChatInterface()
        ```
    """

    def __init__(
        self,
        phone: str,
        config: Optional[ChatConfig] = None,
        style: Optional[ChatStyle] = None,
    ):
        """
        Initialize the Chat interface.

        Args:
            api_key (str): OpenAI API key
            assistant_id (str): OpenAI assistant ID
            config (Optional[ChatConfig]): Chat configuration settings
            style (Optional[ChatStyle]): Chat style settings
        """
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
        """Export conversation to a formatted txt file"""
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
                timestamp = msg["timestamp"].strftime("%H:%M:%S")
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
                timestamp = msg["timestamp"].strftime("%H:%M:%S")
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
            timestamp = msg["timestamp"].strftime("%H:%M:%S")

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
        """
        Add a message to both the UI messages list and thread.

        Args:
            content (str): Message content
            role (str): Message role ('user' or 'assistant')
        """
        message = {"role": role, "content": content, "timestamp": datetime.now()}
        self.messages.append(message)
        # self.thread.addMessage(content=content, role=role)

    def addStyleToMessage(self, message: str, role: str) -> str:
        """
        Add HTML/CSS styling to a message based on its role.

        Args:
            message (str): Message content
            role (str): Message role ('user' or 'assistant')

        Returns:
            str: Styled message HTML
        """
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

    def displayMessages(self, chat_container) -> None:
        """Display all messages in the Streamlit container"""
        with chat_container:
            for msg in self._get_messages():
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

    def exportConversation(
        self, format: str = "txt", output_path: str = None, metadata: dict = None
    ) -> str:
        """
        Export the conversation to a file in the specified format.

        Args:
            format (str): Output format ('txt', 'md', or 'pdf')
            output_path (str, optional): Path to save the file
            metadata (dict, optional): Additional conversation metadata
                Example:
                {
                    'User': 'John Doe',
                    'Branch': 'Main Store',
                    'Address': '123 Main St',
                    'Location': 'City Center'
                }

        Returns:
            str: Path to the exported file

        Raises:
            ValueError: If format is not 'txt', 'md', or 'pdf'
        """
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
        """
        Process the next prompt in the queue.

        Returns:
            bool: True if a message was processed, False otherwise
        """
        if self.prompts_queue:  # and not self.thread.isRunActive():
            # Pop the first prompt from the queue
            # It has already been added to the thread by the processUserInput method
            message = self.prompts_queue.pop(0)

            # Process in thread
            with st.spinner(self.config.loading_text):
                # self.thread.runWithStreaming(self.assistant_id, handlers)
                response = requests.post(
                    f"{DJANGO_API_URL}/conversations/reply/",
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

    def renderChatInterface(self) -> None:
        """
        Render the complete chat interface in Streamlit.

        This method sets up the header, message display area, and input field.
        It should be called after initializing the Chat instance.
        """
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
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)

        # Chat container - display messages
        chat_container = st.container()
        self.displayMessages(chat_container)

        # Chat input
        st.chat_input(
            placeholder=self.config.input_placeholder,
            disabled=self.is_processing,
            key="chat_input",
            on_submit=lambda: self.processUserInput(st.session_state.chat_input),
        )

    # def streamResponse(self, content: str, role: str) -> None:
    #     """
    #     Stream a response character by character with animation.

    #     Args:
    #         content (str): Message content to stream
    #         role (str): Message role ('user' or 'assistant')
    #     """
    #     if role == "user":
    #         _, right = st.columns(USER_CHAT_COLUMNS)
    #         with right:
    #             with st.chat_message(role, avatar=self.config.user_avatar_path):
    #                 container = st.empty()
    #                 current_text = ""
    #                 for char in content:
    #                     current_text += char
    #                     current_text_styled = self.addStyleToMessage(current_text, role)
    #                     container.write(current_text_styled, unsafe_allow_html=True)
    #                     time.sleep(0.01)
    #     else:
    #         left, _ = st.columns(BOT_CHAT_COLUMNS)
    #         with left:
    #             with st.chat_message(role, avatar=self.config.bot_avatar_path):
    #                 container = st.empty()
    #                 current_text = ""
    #                 for char in content:
    #                     current_text += char
    #                     current_text_styled = self.addStyleToMessage(current_text, role)
    #                     container.write(current_text_styled, unsafe_allow_html=True)
    #                     time.sleep(0.01)

    def sendConversationEmail(
        self,
        from_email: str,
        to_email: str,
        password: str,
        attachments: List[str],
        metadata: dict,
    ):
        """
        Sends an email with the conversation report and attachments.

        Args:
            from_email (str): Sender's email address
            to_email (str): Recipient's email address
            password (str): Sender's email account password
            attachments (List[str]): List of file paths to attach
            metadata (dict): Conversation metadata

        Raises:
            Exception: If an error occurs while sending the email
        """
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
        """Compute chat elapsed time based on message timestamps"""
        if len(self._get_messages()) < 2:
            return "Menos de 1 minuto"

        start_time = self._get_messages()[0]["timestamp"]
        end_time = self._get_messages()[-1]["timestamp"]
        duration = end_time - start_time

        minutes = duration.total_seconds() / 60
        if minutes < 1:
            return "Menos de 1 minuto"
        elif minutes < 60:
            return f"{int(minutes)} minutos"
        else:
            hours = minutes / 60
            return f"{int(hours)} horas {int(minutes % 60)} minutos"
