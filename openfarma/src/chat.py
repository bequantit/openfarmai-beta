"""
This module provides a comprehensive chat interface for the OpenFarma AI Assistant, integrating 
with OpenAI's Assistant API through the Thread class for conversational AI capabilities. It 
includes message management, conversation export functionality, and a complete Streamlit-based 
user interface.

Key Components:
- Chat: Main chat interface handler that manages the conversation flow, message processing,
  and UI rendering. Integrates with Thread for AI responses and provides export capabilities.
- ChatConfig: Configuration dataclass for customizing the chat interface appearance and behavior.
- ChatStyle: CSS styling dataclass for customizing the visual appearance of the chat interface.
- PromptTracker: Utility for tracking and reporting user prompts and conversation metrics.

Integration with Thread:
- Chat uses Thread for all OpenAI Assistant interactions
- Messages are sent to Thread for AI processing
- Streaming responses are handled through Thread's EventHandler
- Conversation state is maintained in both Chat and Thread instances

Typical Usage:
1. Create ChatConfig and ChatStyle instances for customization
2. Initialize Chat with API key, assistant ID, and configuration
3. Call renderChatInterface() to display the chat UI
4. Use exportConversation() to save conversations in various formats
5. Integrate with PromptTracker for conversation analytics

This module is designed for production use in pharmaceutical assistance applications,
providing a robust, customizable chat interface with comprehensive export and tracking capabilities.
"""

import io, os
import time, base64
import smtplib
import streamlit as st
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

def encodeImage(image_path: str) -> str:
    """
    Encode an image file to base64 string for embedding in HTML/CSS.

    This utility function converts image files to base64-encoded strings, allowing
    them to be embedded directly in HTML or CSS without requiring external file
    references. This is particularly useful for Streamlit applications where
    images need to be displayed in custom HTML components.

    Args:
        image_path (str): Path to the image file to encode. Supports common image
            formats like PNG, JPEG, GIF, etc.

    Returns:
        str: Base64-encoded string representation of the image, prefixed with
            "data:image/png;base64," for direct use in HTML img tags.

    Raises:
        FileNotFoundError: If the image file doesn't exist at the specified path.
        Exception: If there's an error reading or encoding the image.

    Examples:
        # Basic usage for header logo
        >>> logo_b64 = encodeImage("images/logo.png")
        >>> st.markdown(f'<img src="data:image/png;base64,{logo_b64}">', unsafe_allow_html=True)

        # Error handling
        >>> try:
        ...     image_b64 = encodeImage("nonexistent.png")
        ... except FileNotFoundError:
        ...     print("Image file not found")
        ... except Exception as e:
        ...     print(f"Error encoding image: {e}")

    Use Cases:
        - Embedding images in Streamlit markdown
        - Creating self-contained HTML components
        - Including images in exported documents
        - Custom UI styling with embedded graphics

    Note:
        - Images are converted to PNG format for consistency
        - Base64 encoding increases file size by approximately 33%
        - Large images may impact performance when embedded
        - Useful for creating portable, self-contained applications
    """
    image = Image.open(image_path)
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

@dataclass
class ChatStyle:
    """
    ChatStyle manages comprehensive CSS styling for the OpenFarma chat interface.

    This dataclass provides a complete styling system for the chat interface, including
    message containers, user/bot message differentiation, header layout, and responsive
    design elements. It's designed to create a professional, pharmaceutical-themed
    chat experience.

    Responsibilities:
    - Defines visual styling for chat messages (user and bot)
    - Configures header layout and branding elements
    - Manages Streamlit component visibility and layout
    - Provides responsive design for different screen sizes
    - Ensures consistent branding and user experience

    Styling Features:
    - Custom message bubbles with dotted borders and brand colors
    - Fixed header with logo and caption
    - Hidden Streamlit UI elements for clean interface
    - Responsive layout with proper spacing and alignment
    - Brand-consistent color scheme (#8EA749 green theme)
    - Custom font sizes and typography

    CSS Components:
    - Message containers: .bot-message, .user-message
    - Header elements: .fixed-header, .header-content, .header-image
    - Layout containers: .chat-container, .main .block-container
    - Streamlit overrides: Hidden toolbars, decorations, status widgets

    Examples:
        # Use default styling
        >>> style = ChatStyle()
        >>> chat = Chat(api_key, assistant_id, style=style)

        # Custom styling with modifications
        >>> custom_style = ChatStyle()
        >>> custom_style.style = custom_style.style.replace("#8EA749", "#2E8B57")
        >>> chat = Chat(api_key, assistant_id, style=custom_style)

    Brand Colors:
        - Primary Green: #8EA749 (message borders)
        - Background: #FFFFFF (white)
        - Text: #000000 (black)
        - Header: #FFFFFF (white background)

    Note:
        - CSS is embedded directly in the Streamlit app
        - Styling is applied globally to the chat interface
        - Custom modifications can be made by editing the style string
        - Responsive design adapts to different screen sizes
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
    ChatConfig provides comprehensive configuration settings for the OpenFarma chat interface.

    This dataclass centralizes all configurable aspects of the chat interface, including
    branding, messaging, file paths, and user experience elements. It allows for easy
    customization of the chat interface without modifying the core Chat class logic.

    Responsibilities:
    - Defines branding elements (title, header caption, logos)
    - Configures avatar images for user and bot messages
    - Sets user interface text (placeholders, loading messages)
    - Manages file paths for images and assets
    - Provides default values for all configurable elements

    Configuration Elements:
    - Branding: Title, header caption, logo paths
    - Avatars: User and bot avatar images
    - UI Text: Input placeholders, loading messages
    - File Paths: All image and asset locations

    Examples:
        # Use default configuration
        >>> config = ChatConfig()
        >>> chat = Chat(api_key, assistant_id, config=config)

        # Custom configuration for different branding
        >>> custom_config = ChatConfig(
        ...     title="🏥 Hospital Assistant",
        ...     header_caption="Asistente médico virtual",
        ...     header_logo_path="assets/hospital_logo.png",
        ...     user_avatar_path="assets/doctor_avatar.png",
        ...     bot_avatar_path="assets/ai_avatar.png",
        ...     input_placeholder="Describa sus síntomas...",
        ...     loading_text="Analizando su consulta..."
        ... )
        >>> chat = Chat(api_key, assistant_id, config=custom_config)

        # Minimal configuration with custom paths
        >>> config = ChatConfig(
        ...     header_logo_path="images/company_logo.png",
        ...     user_avatar_path="images/user_icon.png",
        ...     bot_avatar_path="images/bot_icon.png"
        ... )

    File Path Requirements:
        - All image paths should be relative to the application root
        - Supported formats: PNG, JPEG, GIF
        - Images should be appropriately sized for their use
        - Header logo: Recommended 200x80px
        - Avatars: Recommended 64x64px

    Note:
        - Default values provide a complete working configuration
        - All paths should be validated before use
        - Configuration can be loaded from external files
        - Changes to configuration require re-initialization of Chat
    """
    title: str = "💬 openfarmAI"
    header_caption: str = "Tu asistente farmacéutico virtual"
    header_logo_path: str = "path/to/header/logo"
    user_avatar_path: str = "path/to/user/avatar"
    bot_avatar_path: str = "path/to/bot/avatar"
    input_placeholder: str = "Escriba su consulta aquí..."
    loading_text: str = "Buscando información..."

class Chat:
    """
    Chat is the main interface handler for the OpenFarma AI Assistant, providing a complete
    conversational AI experience with comprehensive message management, export capabilities,
    and Streamlit-based user interface.

    This class serves as the central orchestrator for the chat application, integrating
    with OpenAI's Assistant API through the Thread class for AI responses, managing
    conversation state, and providing extensive export and tracking functionality.

    Responsibilities:
    - Manages the complete chat interface and user experience
    - Integrates with Thread for OpenAI Assistant interactions
    - Handles message processing, queuing, and streaming
    - Provides conversation export in multiple formats (TXT, MD, PDF)
    - Manages conversation state and message history
    - Integrates with PromptTracker for analytics and reporting
    - Supports email export with attachments and metadata

    Integration with Thread:
    - Uses Thread for all OpenAI Assistant API interactions
    - Messages are sent to Thread for AI processing and responses
    - Streaming responses are handled through Thread's EventHandler
    - Conversation state is synchronized between Chat and Thread
    - Thread handles tool calls and function execution

    Key Features:
    - Real-time streaming chat interface
    - Message queuing and processing management
    - Comprehensive export capabilities (TXT, MD, PDF)
    - Email export with conversation reports
    - Conversation analytics and tracking
    - Customizable styling and branding
    - Responsive design and mobile compatibility

    Examples:
        # Basic usage with default configuration
        >>> chat = Chat(api_key, assistant_id)
        >>> chat.renderChatInterface()

        # Custom configuration
        >>> config = ChatConfig(
        ...     title="🏥 Medical Assistant",
        ...     header_logo_path="assets/logo.png"
        ... )
        >>> chat = Chat(api_key, assistant_id, config=config)
        >>> chat.renderChatInterface()

        # Export conversation
        >>> chat.exportConversation(
        ...     format="pdf",
        ...     metadata={"User": "Dr. Smith", "Branch": "Main Hospital"}
        ... )

    Message Flow:
        1. User input is captured and added to messages
        2. Message is queued for processing
        3. Thread processes message with OpenAI Assistant
        4. AI response is streamed back to user
        5. Response is added to conversation history
        6. PromptTracker updates analytics

    Export Capabilities:
        - TXT: Plain text format with timestamps
        - MD: Markdown with embedded logo and formatting
        - PDF: Professional PDF with header logo and metadata
        - Email: HTML email with attachments and conversation summary

    Note:
        - Designed for production use in pharmaceutical applications
        - Integrates seamlessly with OpenAI Assistant API
        - Provides comprehensive conversation management
        - Supports multiple export formats for compliance and reporting
        - Includes analytics and tracking for business intelligence
    """

    def __init__(
            self, 
            api_key: str, 
            assistant_id: str, 
            config: Optional[ChatConfig] = None, 
            style: Optional[ChatStyle] = None):
        """
        Initialize the Chat interface with OpenAI integration and configuration.

        This method sets up the complete chat interface, including OpenAI integration,
        message management, styling, and configuration. It creates a new Thread instance
        for handling AI interactions and initializes the conversation with a welcome message.

        Args:
            api_key (str): Your OpenAI API key for authentication and assistant access.
            assistant_id (str): The unique identifier of the OpenAI assistant to use.
                Example: "asst_abc123def456"
            config (Optional[ChatConfig]): Configuration settings for the chat interface.
                If None, default configuration is used.
            style (Optional[ChatStyle]): CSS styling for the chat interface.
                If None, default styling is used.

        Raises:
            Exception: If Thread initialization fails due to API errors or invalid credentials.

        Initialization Process:
            1. Set up configuration and styling (use defaults if not provided)
            2. Initialize message storage and conversation state
            3. Create Thread instance for OpenAI integration
            4. Set up message processing queue and tracking
            5. Add welcome message to start conversation

        Examples:
            # Basic initialization with defaults
            >>> chat = Chat("sk-...", "asst_123")
            >>> print(f"Chat initialized with assistant: {chat.assistant_id}")

            # Custom configuration
            >>> config = ChatConfig(
            ...     title="🏥 Medical Assistant",
            ...     header_caption="Asistente médico virtual"
            ... )
            >>> chat = Chat("sk-...", "asst_456", config=config)

            # Full customization
            >>> config = ChatConfig(header_logo_path="assets/logo.png")
            >>> style = ChatStyle()
            >>> chat = Chat("sk-...", "asst_789", config=config, style=style)

        Internal State:
            - config: ChatConfig instance for interface settings
            - style: ChatStyle instance for CSS styling
            - messages: List of conversation messages with timestamps
            - thread: Thread instance for OpenAI integration
            - assistant_id: OpenAI assistant identifier
            - is_processing: Flag for message processing status
            - prompts_queue: Queue for pending user messages
            - prompt_tracker: PromptTracker for analytics

        Welcome Message:
            A default welcome message is automatically added to start the conversation:
            "Hola, ¿en qué te puedo ayudar?"

        Note:
            - API key should be kept secure and not logged
            - Assistant ID must be valid and accessible
            - Configuration and styling can be modified after initialization
            - Thread is created fresh for each Chat instance
            - Welcome message is added to both UI and Thread
        """
        self.config = config or ChatConfig()
        self.style = style or ChatStyle()
        self.messages: List[Dict[str, str]] = []
        self.thread = Thread(api_key)
        self.assistant_id = assistant_id
        self.is_processing = False
        self.prompts_queue: List[str] = []
        self.prompt_tracker = PromptTracker()
        
        # Initialize with welcome message
        self.addMessage("Hola, ¿en qué te puedo ayudar?", "assistant")

    def _exportToTxt(self, output_path: str, metadata: dict) -> str:
        """
        Export conversation to a formatted plain text file.

        This method creates a human-readable text file containing the complete conversation
        with timestamps, metadata, and proper formatting. The output is designed for
        easy reading and archiving purposes.

        Args:
            output_path (str): Path where the text file will be saved.
                Example: "conversations/chat_20241201_143022.txt"
            metadata (dict): Additional information to include in the export.
                Example: {"User": "Dr. Smith", "Branch": "Main Hospital"}

        Returns:
            str: The path to the created text file.

        Raises:
            IOError: If there's an error writing to the file.
            Exception: If there's an error during file creation.

        File Format:
            The exported text file contains:
            - Header with export timestamp
            - Metadata section with user information
            - Chronological conversation with timestamps
            - Clear separation between messages

        Examples:
            # Basic export
            >>> metadata = {"User": "John Doe", "Branch": "Downtown"}
            >>> file_path = chat._exportToTxt("chat_export.txt", metadata)
            >>> print(f"Exported to: {file_path}")

            # Export with comprehensive metadata
            >>> metadata = {
            ...     "User": "Dr. Maria Garcia",
            ...     "Branch": "Central Hospital",
            ...     "Department": "Pharmacy",
            ...     "Session ID": "SESS_12345"
            ... }
            >>> chat._exportToTxt("medical_consultation.txt", metadata)

        Output Structure:
            ```
            Chat Export - 2024-12-01 14:30:22
            ==================================================

            INFORMACIÓN
            --------------------------------------------------
            User: Dr. Maria Garcia
            Branch: Central Hospital
            Department: Pharmacy
            --------------------------------------------------

            [Usuario - 14:30:25]
            ¿Cuáles son los efectos secundarios del paracetamol?
            --------------------------------------------------

            [Asistente - 14:30:28]
            Los efectos secundarios más comunes del paracetamol incluyen...
            --------------------------------------------------
            ```

        Use Cases:
            - Archiving conversations for compliance
            - Creating readable conversation logs
            - Sharing conversations via email
            - Backup and record keeping

        Note:
            - File is saved in UTF-8 encoding for international character support
            - Timestamps are in local timezone
            - Empty metadata fields are automatically filtered out
            - File path should be writable by the application
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"Chat Export - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 50 + "\n\n")
            
            # Add metadata
            f.write("INFORMACIÓN\n")
            f.write("-" * 50 + "\n")
            for key, value in metadata.items():
                if value:  # Only write if value is not empty
                    f.write(f"{key}: {value}\n")
            f.write("-" * 50 + "\n\n")
            
            for msg in self.messages:
                role = "Usuario" if msg["role"] == "user" else "Asistente"
                timestamp = msg["timestamp"].strftime("%H:%M:%S")
                f.write(f"[{role} - {timestamp}]\n")
                f.write(f"{msg['content']}\n")
                f.write("-" * 50 + "\n\n")
        
        return output_path

    def _exportToMd(self, output_path: str, metadata: dict) -> str:
        """Export conversation to a markdown file with header logo"""
        with open(output_path, 'w', encoding='utf-8') as f:
            # Add header logo as base64 image
            with open(self.config.header_logo_path, "rb") as img_file:
                b64_image = base64.b64encode(img_file.read()).decode()
                f.write(f'<img src="data:image/png;base64,{b64_image}" width="150px" align="left"/>\n\n')
            
            f.write(f"# ChatBot - Conversación - {datetime.now().strftime('%Y-%m-%d')}\n\n")
            
            # Add metadata
            f.write("## Información\n\n")
            for key, value in metadata.items():
                if value:  # Only write if value is not empty
                    f.write(f"- **{key}:** {value}\n")
            f.write("\n---\n\n")
            
            for msg in self.messages:
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
        pdf.image(self.config.header_logo_path, x=10, y=10, w=40)  # Adjust w=40 to change logo size
        pdf.ln(30)  # Space after logo
        
        # Configure fonts and add title
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, f"ChatBot - Conversación - {datetime.now().strftime('%Y-%m-%d')}", ln=True)
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
        for msg in self.messages:
            role = "Usuario" if msg["role"] == "user" else "Asistente"
            timestamp = msg["timestamp"].strftime("%H:%M:%S")
            
            # Role header with timestamp
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 10, f"{role} - {timestamp}:", ln=True)
            
            # Message content
            pdf.set_font("Arial", size=12)
            pdf.multi_cell(0, 10, msg['content'])
            pdf.ln(5)
            
            # Separator line
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(10)
        
        pdf.output(output_path)
        return output_path
    
    def addMessage(self, content: str, role: str) -> None:
        """
        Add a message to both the UI messages list and the OpenAI thread.

        This method is the primary way to add messages to the conversation. It ensures
        that messages are properly stored in both the local UI state and the OpenAI
        thread for AI processing. Messages include timestamps for chronological tracking.

        Args:
            content (str): The message content to add. Can be user input or AI response.
            role (str): The role of the message sender. Must be "user" or "assistant".

        Returns:
            None. The message is added to both local storage and OpenAI thread.

        Raises:
            Exception: If there's an error adding the message to the OpenAI thread.

        Message Structure:
            Each message is stored as a dictionary containing:
            - role: "user" or "assistant"
            - content: The message text
            - timestamp: DateTime when the message was added

        Examples:
            # Add user message
            >>> chat.addMessage("¿Cuáles son los efectos del ibuprofeno?", "user")

            # Add assistant response
            >>> chat.addMessage("El ibuprofeno es un antiinflamatorio que...", "assistant")

            # Add system-generated message
            >>> chat.addMessage("Conversación iniciada", "assistant")

        Integration with Thread:
            - Message is added to local messages list for UI display
            - Message is sent to OpenAI thread for AI processing
            - Timestamp is automatically added for tracking
            - Message becomes part of conversation history

        Use Cases:
            - Adding user input from chat interface
            - Storing AI responses from OpenAI
            - Adding system messages or notifications
            - Building conversation history for export

        Note:
            - Role must be "user" or "assistant" (no "system" role in OpenAI Assistant API)
            - Messages are added chronologically with timestamps
            - Content should be properly formatted for display
            - Thread integration ensures AI context is maintained
        """
        message = {
            "role": role, 
            "content": content,
            "timestamp": datetime.now()
        }
        self.messages.append(message)
        self.thread.addMessage(content=content, role=role)

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
        self.thread = Thread(self.thread.api_key)
        self.addMessage("Hola, ¿en qué te puedo ayudar?", "assistant")

    def displayMessages(self, chat_container) -> None:
        """Display all messages in the Streamlit container"""
        with chat_container:
            for msg in self.messages:
                if msg["role"] == "user":
                    _, right = st.columns(USER_CHAT_COLUMNS)
                    with right:
                        with st.chat_message(msg["role"], avatar=self.config.user_avatar_path):
                            message = self.addStyleToMessage(msg["content"], msg["role"])
                            st.write(message, unsafe_allow_html=True)
                else:
                    left, _ = st.columns(BOT_CHAT_COLUMNS)
                    with left:
                        with st.chat_message(msg["role"], avatar=self.config.bot_avatar_path):
                            message = self.addStyleToMessage(msg["content"], msg["role"])
                            st.write(message, unsafe_allow_html=True)

    def exportConversation(self, format: str = "txt", output_path: str = None, metadata: dict = None) -> str:
        """
        Export the conversation to a file in the specified format with metadata.

        This method provides comprehensive conversation export capabilities in multiple
        formats, including plain text, markdown, and PDF. It's designed for compliance,
        archiving, and sharing purposes in pharmaceutical applications.

        Args:
            format (str): Output format for the export. Valid options: "txt", "md", "pdf".
                Defaults to "txt".
            output_path (str, optional): Custom path for the exported file.
                If None, a timestamped filename is generated automatically.
                Example: "exports/consultation_20241201.pdf"
            metadata (dict, optional): Additional information to include in the export.
                Example: {
                    "User": "Dr. Maria Garcia",
                    "Branch": "Central Hospital",
                    "Department": "Pharmacy",
                    "Patient ID": "PAT_12345"
                }

        Returns:
            str: Path to the exported file.

        Raises:
            ValueError: If format is not supported ("txt", "md", or "pdf").
            Exception: If there's an error during file creation or export.

        Supported Formats:
            - "txt": Plain text with timestamps and metadata
            - "md": Markdown with embedded logo and formatting
            - "pdf": Professional PDF with header logo and structured layout

        Examples:
            # Basic text export
            >>> file_path = chat.exportConversation("txt")
            >>> print(f"Exported to: {file_path}")

            # PDF export with metadata
            >>> metadata = {
            ...     "User": "Dr. Smith",
            ...     "Branch": "Main Hospital",
            ...     "Consultation Type": "Medication Review"
            ... }
            >>> pdf_path = chat.exportConversation("pdf", metadata=metadata)

            # Custom path markdown export
            >>> md_path = chat.exportConversation(
            ...     format="md",
            ...     output_path="reports/medical_consultation.md",
            ...     metadata={"User": "Nurse Johnson"}
            ... )

            # Error handling
            >>> try:
            ...     path = chat.exportConversation("docx")  # Unsupported format
            ... except ValueError as e:
            ...     print(f"Format error: {e}")

        File Naming:
            If no output_path is provided, files are named with timestamp:
            - txt: "chat_export_20241201_143022.txt"
            - md: "chat_export_20241201_143022.md"
            - pdf: "chat_export_20241201_143022.pdf"

        Metadata Integration:
            - All formats include metadata section
            - Empty metadata fields are automatically filtered
            - Metadata appears at the beginning of the export
            - Supports custom fields for different use cases

        Use Cases:
            - Compliance reporting and record keeping
            - Sharing conversations with healthcare providers
            - Archiving patient consultations
            - Quality assurance and training
            - Legal documentation and audit trails

        Note:
            - PDF export requires FPDF library
            - Markdown export includes embedded logo
            - All exports include timestamps and conversation flow
            - File paths should be writable by the application
            - Large conversations may take time to export
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

    def processQueue(self, handlers) -> bool:
        """
        Process the next prompt in the queue using OpenAI Assistant.

        This method handles the asynchronous processing of user messages by taking
        the next prompt from the queue and sending it to the OpenAI Assistant through
        the Thread instance. It manages the streaming response and updates the
        conversation state accordingly.

        Args:
            handlers: Callback handlers for message processing, typically tool handlers
                for function calling capabilities. Passed to Thread.runWithStreaming().

        Returns:
            bool: True if a message was processed, False if queue is empty or thread is busy.

        Raises:
            Exception: If there's an error during message processing or AI response generation.

        Processing Flow:
            1. Check if there are queued prompts and thread is not busy
            2. Remove the next prompt from the queue
            3. Send prompt to OpenAI Assistant via Thread
            4. Stream the AI response in real-time
            5. Add the response to conversation history
            6. Update processing status and analytics

        Examples:
            # Basic queue processing
            >>> if chat.processQueue(handlers):
            ...     print("Message processed successfully")
            ... else:
            ...     print("No messages to process or thread is busy")

            # Process with custom handlers
            >>> tool_handlers = {
            ...     "get_medication_info": medication_handler,
            ...     "check_interactions": interaction_handler
            ... }
            >>> chat.processQueue(tool_handlers)

            # Error handling
            >>> try:
            ...     processed = chat.processQueue(handlers)
            ...     if processed:
            ...         print("Message processed")
            ... except Exception as e:
            ...     print(f"Processing error: {e}")

        Queue Management:
            - Messages are processed in FIFO (First In, First Out) order
            - Only one message is processed per call
            - Thread must not be active for processing to occur
            - Processing status is updated automatically

        Integration with Thread:
            - Uses Thread.runWithStreaming() for real-time responses
            - Handlers are passed through to Thread for tool calling
            - Response is retrieved from Thread and added to conversation
            - Thread state is managed automatically

        Analytics Integration:
            - PromptTracker is updated after successful processing
            - Conversation metrics are maintained
            - Processing status affects UI state

        Note:
            - This method is typically called in a loop or event handler
            - Handlers should be thread-safe and handle errors gracefully
            - Streaming provides real-time user experience
            - Queue processing prevents message loss during busy periods
        """
        if self.prompts_queue and not self.thread.isRunActive():
            # Pop the first prompt from the queue
            # It has already been added to the thread by the processUserInput method
            self.prompts_queue.pop(0)
            
            # Process in thread
            with st.spinner(self.config.loading_text):
                self.thread.runWithStreaming(self.assistant_id, handlers)

            # Get and add assistant response
            response = self.thread.retrieveLastMessage()
            content = response["content"][0].text.value
            self.addMessage(content, "assistant")
            
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
        Render the complete chat interface in Streamlit with header, messages, and input.

        This method creates the full chat interface including the fixed header with logo,
        message display area, and chat input field. It applies the configured styling
        and sets up the interactive components for user interaction.

        Returns:
            None. The interface is rendered directly in the Streamlit app.

        Raises:
            Exception: If there's an error rendering the interface or loading images.

        Interface Components:
            1. Fixed Header: Logo and caption at the top of the page
            2. Message Display: Container showing conversation history
            3. Chat Input: Text input field for user messages
            4. Styling: Applied CSS for professional appearance

        Examples:
            # Basic interface rendering
            >>> chat = Chat(api_key, assistant_id)
            >>> chat.renderChatInterface()

            # Custom configuration rendering
            >>> config = ChatConfig(
            ...     header_logo_path="assets/logo.png",
            ...     header_caption="Asistente médico virtual"
            ... )
            >>> chat = Chat(api_key, assistant_id, config=config)
            >>> chat.renderChatInterface()

            # Error handling
            >>> try:
            ...     chat.renderChatInterface()
            ... except Exception as e:
            ...     st.error(f"Error rendering interface: {e}")

        Header Features:
            - Fixed position at top of page
            - Embedded logo image (base64 encoded)
            - Customizable caption text
            - Professional styling and layout

        Message Display:
            - Shows all conversation messages
            - User and bot messages are visually differentiated
            - Messages include timestamps and proper formatting
            - Responsive layout for different screen sizes

        Input Field:
            - Placeholder text from configuration
            - Disabled during message processing
            - Automatic message handling on submit
            - Custom styling for better UX

        Styling Integration:
            - Applies ChatStyle CSS rules
            - Hides Streamlit UI elements for clean interface
            - Responsive design for mobile and desktop
            - Brand-consistent color scheme

        Use Cases:
            - Main chat application interface
            - Customer support chat systems
            - Medical consultation interfaces
            - Educational AI assistants

        Note:
            - Must be called after Chat initialization
            - Interface is rendered in the current Streamlit session
            - Header logo should be accessible at configured path
            - Styling is applied globally to the chat interface
            - Input field automatically handles user submissions
        """
        # Header
        header_logo = encodeImage(self.config.header_logo_path)
        st.markdown(f"""
            <div class="fixed-header">
                <div class="header-content">
                    <img src="data:image/jpeg;base64,{header_logo}" class="header-image">
                </div>
            </div>
        """, unsafe_allow_html=True)
        st.markdown(f"""<div class="header-caption">{self.config.header_caption}</div>""", unsafe_allow_html=True)
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)

        # Chat container - display messages
        chat_container = st.container()
        self.displayMessages(chat_container)

        # Chat input
        st.chat_input(
            placeholder=self.config.input_placeholder,
            disabled=self.is_processing,
            key="chat_input",
            on_submit=lambda: self.processUserInput(st.session_state.chat_input)
        )

    def streamResponse(self, content: str, role: str) -> None:
        """
        Stream a response character by character with animation.
        
        Args:
            content (str): Message content to stream
            role (str): Message role ('user' or 'assistant')
        """
        if role == "user":
            _, right = st.columns(USER_CHAT_COLUMNS)
            with right:
                with st.chat_message(role, avatar=self.config.user_avatar_path):
                    container = st.empty()
                    current_text = ""
                    for char in content:
                        current_text += char
                        current_text_styled = self.addStyleToMessage(current_text, role)
                        container.write(current_text_styled, unsafe_allow_html=True)
                        time.sleep(0.01)
        else:
            left, _ = st.columns(BOT_CHAT_COLUMNS)
            with left:
                with st.chat_message(role, avatar=self.config.bot_avatar_path):
                    container = st.empty()
                    current_text = ""
                    for char in content:
                        current_text += char
                        current_text_styled = self.addStyleToMessage(current_text, role)
                        container.write(current_text_styled, unsafe_allow_html=True)
                        time.sleep(0.01)

    def sendConversationEmail(self, from_email: str, to_email: str, password: str, 
                              attachments: List[str], metadata: dict):
        """
        Send an email with conversation report and attachments.

        This method creates and sends a professional HTML email containing a summary
        of the conversation, metadata, and attached files. It's designed for sharing
        consultation reports, compliance documentation, and conversation archives.

        Args:
            from_email (str): Sender's email address. Must be a valid Gmail account.
                Example: "reports@openfarma.com"
            to_email (str): Recipient's email address.
                Example: "doctor.smith@hospital.com"
            password (str): Sender's email account password or app-specific password.
                Note: Use app-specific passwords for security.
            attachments (List[str]): List of file paths to attach to the email.
                Example: ["chat_export.pdf", "consultation_report.txt"]
            metadata (dict): Conversation metadata to include in the email body.
                Example: {
                    "User": "Dr. Maria Garcia",
                    "Branch": "Central Hospital",
                    "Patient ID": "PAT_12345"
                }

        Returns:
            None. Email is sent via SMTP.

        Raises:
            smtplib.SMTPAuthenticationError: If email credentials are invalid.
            smtplib.SMTPConnectError: If connection to SMTP server fails.
            Exception: If there's an error sending the email or attaching files.

        Email Features:
            - Professional HTML formatting
            - Conversation summary and statistics
            - Metadata display in organized format
            - Multiple file attachments support
            - Automatic timestamp and duration calculation
            - Branded footer with company information

        Examples:
            # Basic email with PDF attachment
            >>> metadata = {"User": "Dr. Smith", "Branch": "Main Hospital"}
            >>> attachments = ["consultation.pdf"]
            >>> chat.sendConversationEmail(
            ...     from_email="reports@openfarma.com",
            ...     to_email="doctor@hospital.com",
            ...     password="app_password_123",
            ...     attachments=attachments,
            ...     metadata=metadata
            ... )

            # Multiple attachments with comprehensive metadata
            >>> metadata = {
            ...     "User": "Nurse Johnson",
            ...     "Branch": "Emergency Department",
            ...     "Patient ID": "PAT_789",
            ...     "Consultation Type": "Medication Review"
            ... }
            >>> attachments = ["chat_export.pdf", "medication_list.txt", "interaction_report.pdf"]
            >>> chat.sendConversationEmail(
            ...     from_email="nursing@hospital.com",
            ...     to_email="pharmacist@hospital.com",
            ...     password="secure_password",
            ...     attachments=attachments,
            ...     metadata=metadata
            ... )

            # Error handling
            >>> try:
            ...     chat.sendConversationEmail(from_email, to_email, password, attachments, metadata)
            ...     print("Email sent successfully")
            ... except smtplib.SMTPAuthenticationError:
            ...     print("Authentication failed. Check email and password.")
            ... except Exception as e:
            ...     print(f"Email sending failed: {e}")

        Email Content:
            The email includes:
            - Professional header with company branding
            - Conversation metadata and statistics
            - Message count and duration information
            - Attachment list and count
            - Privacy notice and footer
            - Beta version disclaimer

        SMTP Configuration:
            - Uses Gmail SMTP server (smtp.gmail.com:587)
            - Requires TLS encryption
            - Supports app-specific passwords
            - Handles authentication errors gracefully

        Security Considerations:
            - Use app-specific passwords instead of account passwords
            - Store credentials securely (not in code)
            - Consider using environment variables for sensitive data
            - Email content may contain sensitive medical information

        Use Cases:
            - Sharing consultation reports with healthcare providers
            - Compliance documentation and record keeping
            - Quality assurance and peer review
            - Patient care coordination
            - Legal documentation and audit trails

        Note:
            - Gmail account must have 2FA enabled for app passwords
            - Large attachments may take time to send
            - Email content is HTML-formatted for professional appearance
            - Conversation details are in attachments for privacy
            - Beta version disclaimer is included automatically
        """
        try:

            # Email settings
            message = MIMEMultipart()
            message['From'] = from_email
            message['To'] = to_email
            message['Subject'] = f'Dev:Reporte de Conversación OpenFarma - {datetime.now().strftime("%Y-%m-%d %H:%M")}'

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
                        <li><strong>Usuario:</strong> {metadata.get('Usuario', 'No especificado')}</li>
                        <li><strong>Sucursal:</strong> {metadata.get('Sucursal', 'No especificada')}</li>
                        <li><strong>Dirección:</strong> {metadata.get('Dirección', 'No especificada')}</li>
                        <li><strong>Localidad:</strong> {metadata.get('Localidad', 'No especificada')}</li>
                    </ul>
                </div>

                <div style="margin-top: 20px;">
                    <h3 style="color: #2c3e50;">Detalles de la Conversación:</h3>
                    <ul>
                        <li>Cantidad de mensajes intercambiados: {len(self.messages)}</li>
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
            message.attach(MIMEText(body, 'html'))

            # Attach files
            for file_path in attachments:
                try:
                    with open(file_path, "rb") as f:
                        part = MIMEApplication(f.read(), _subtype="pdf")
                        part.add_header('Content-Disposition', 'attachment', 
                                      filename=os.path.basename(file_path))
                        message.attach(part)
                except Exception as e:
                    raise Exception(f"Error attaching file {file_path}: {str(e)}")

            # Start SMTP session
            session = smtplib.SMTP('smtp.gmail.com', 587)
            session.starttls()
            session.login(from_email, password)

            # Send email
            text = message.as_string()
            session.sendmail(from_email, to_email, text)
            session.quit()

        except smtplib.SMTPAuthenticationError:
            raise Exception("Authentication error. Check email address and password.")
        except smtplib.SMTPConnectError:
            raise Exception("Failed to connect to SMTP server. Check internet connection.")
        except Exception as e:
            raise Exception(f"Error sending email: {str(e)}")

    def _computeChatElapsedTime(self) -> str:
        """
        Compute the total elapsed time of the conversation based on message timestamps.

        This method calculates the duration between the first and last message in the
        conversation, providing a human-readable string representation of the total
        conversation time. It's used for analytics, reporting, and email summaries.

        Returns:
            str: Human-readable duration string in Spanish.
                Examples: "Menos de 1 minuto", "5 minutos", "2 horas 30 minutos"

        Calculation Logic:
            - Uses first message timestamp as start time
            - Uses last message timestamp as end time
            - Calculates difference in minutes
            - Formats output based on duration length

        Examples:
            # Short conversation
            >>> chat.messages = [
            ...     {"timestamp": datetime(2024, 12, 1, 14, 30, 0)},
            ...     {"timestamp": datetime(2024, 12, 1, 14, 31, 30)}
            ... ]
            >>> duration = chat._computeChatElapsedTime()
            >>> print(duration)  # "1 minutos"

            # Long conversation
            >>> chat.messages = [
            ...     {"timestamp": datetime(2024, 12, 1, 10, 0, 0)},
            ...     {"timestamp": datetime(2024, 12, 1, 12, 30, 0)}
            ... ]
            >>> duration = chat._computeChatElapsedTime()
            >>> print(duration)  # "2 horas 30 minutos"

            # Very short conversation
            >>> chat.messages = [
            ...     {"timestamp": datetime(2024, 12, 1, 14, 30, 0)},
            ...     {"timestamp": datetime(2024, 12, 1, 14, 30, 30)}
            ... ]
            >>> duration = chat._computeChatElapsedTime()
            >>> print(duration)  # "Menos de 1 minuto"

        Duration Categories:
            - Less than 1 minute: "Menos de 1 minuto"
            - 1-59 minutes: "X minutos"
            - 1+ hours: "X horas Y minutos"

        Use Cases:
            - Email conversation summaries
            - Analytics and reporting
            - Conversation efficiency metrics
            - Compliance documentation
            - Quality assurance tracking

        Integration:
            - Used by sendConversationEmail() for email summaries
            - Provides context for conversation analysis
            - Helps with resource allocation and planning
            - Supports performance monitoring

        Note:
            - Requires at least 2 messages for calculation
            - Returns default message for insufficient data
            - Time is calculated in local timezone
            - Output is in Spanish for consistency with application
            - Precision is to the minute level
        """
        if len(self.messages) < 2:
            return "Menos de 1 minuto"
        
        start_time = self.messages[0]["timestamp"]
        end_time = self.messages[-1]["timestamp"]
        duration = end_time - start_time
        
        minutes = duration.total_seconds() / 60
        if minutes < 1:
            return "Menos de 1 minuto"
        elif minutes < 60:
            return f"{int(minutes)} minutos"
        else:
            hours = minutes / 60
            return f"{int(hours)} horas {int(minutes % 60)} minutos"