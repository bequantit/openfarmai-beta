"""
OpenFarma AI Assistant - Main Application Entry Point

This module serves as the main entry point for the OpenFarma AI Assistant application,
providing a comprehensive pharmaceutical assistance system with authentication,
real-time data synchronization, and AI-powered chat capabilities.

Key Features:
- User authentication and session management
- Real-time stock and product data synchronization
- AI-powered chat interface for pharmaceutical assistance
- Automatic data updates and maintenance
- Conversation export and email reporting
- Store-specific data management

Application Flow:
1. Environment setup and path configuration
2. User authentication via login interface
3. Store-specific data synchronization (stock, images, ABM)
4. Chat interface initialization and rendering
5. Real-time data updates and conversation management
6. Session cleanup and conversation export on logout

Dependencies:
- Streamlit: Web application framework
- OpenAI: AI assistant integration
- SQLite: Local database management
- Subprocess: External script execution
- Various OpenFarma modules for specific functionality

Configuration:
- API keys managed through Streamlit secrets
- Database paths and constants from params module
- Environment-specific settings (local vs remote)

Usage:
    Run this file directly with Streamlit:
    streamlit run openfarma/main.py

    Or execute as a Python script:
    python openfarma/main.py
"""

import os
import sys
import time
import subprocess
import streamlit as st
from datetime import datetime

# ------------------ Environment Configuration ------------------

# Flag to determine if running locally or remotely
# Controls SQLite database configuration and path handling
RUN_LOCAL = False

if not RUN_LOCAL:
    # Use pysqlite3 for enhanced SQLite functionality in remote environments
    import pysqlite3
    # Trick to update sqlite - replace the default sqlite3 module with pysqlite3
    CHROMA_DB_PATH = os.path.join(os.getcwd(), "openfarma/database/chroma")
    __import__('pysqlite3')
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
    
    # Configure Django-style database settings for Chroma
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(CHROMA_DB_PATH, 'db.sqlite3'),
        }
    }

# ------------------ Path Configuration ------------------

# Get the absolute path to the project root directory
# This ensures consistent path resolution regardless of execution location
REPO_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Verify that the src directory exists before proceeding
# This is critical for proper module imports
src_path = os.path.join(REPO_DIR, 'src')
if not os.path.exists(src_path):
    raise RuntimeError(f"Source directory not found at {src_path}")

# Add necessary directories to Python path for module imports
# This allows importing from both the main src and openfarma directories
if REPO_DIR not in sys.path:
    sys.path.insert(0, REPO_DIR)
    sys.path.insert(0, os.path.join(REPO_DIR, 'src'))
    sys.path.insert(0, os.path.join(REPO_DIR, 'openfarma'))

# ------------------ Module Imports ------------------

try:
    # Import OpenFarma application modules
    from openfarma.src.login import loginPage
    from openfarma.src.params import *
    from openfarma.src.fc import *
    from openfarma.src.chat import Chat, ChatConfig
except ImportError as e:
    raise ImportError(f"Import error: {e}")

# ------------------ API Configuration ------------------

# Retrieve API keys from Streamlit secrets for secure configuration
# These are required for OpenAI Assistant integration
api_key = st.secrets["OPENFARMA_API_KEY"]
assistant_id = st.secrets["OPENFARMA_ASSISTANT_ID"]

# ------------------ Main Application Function ------------------

def main():
    """
    Main application function that orchestrates the OpenFarma AI Assistant.
    
    This function manages the complete application lifecycle including:
    - Authentication state management
    - Data synchronization for store-specific information
    - Chat interface initialization and rendering
    - Real-time data updates
    - Session cleanup and conversation export
    
    Application States:
    1. Unauthenticated: Shows login interface
    2. Authenticated: Shows chat interface with store information
    
    Data Synchronization:
    - Stock data: Product availability and pricing
    - Images data: Product images and URLs
    - ABM data: Product catalog and descriptions
    
    Real-time Updates:
    - Stock data updates every hour (configurable via STOCK_UPDATE_INTERVAL)
    - Automatic conversation export on logout
    - Prompt tracking and analytics
    
    Sidebar Features:
    - Store information display
    - Logout functionality with conversation export
    - Session state management
    
    Error Handling:
    - Graceful handling of data synchronization failures
    - User-friendly error messages
    - Fallback behavior for missing data
    """
    
    # Initialize authentication state in Streamlit session
    # These variables persist across app reruns
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'username' not in st.session_state:
        st.session_state.username = None

    # ------------------ Authentication Check ------------------
    
    # Check if user is authenticated
    if not st.session_state.authenticated:
        # Show login page for unauthenticated users
        loginPage()
    else:
        # ------------------ Authenticated User Interface ------------------
        
        # Display store information in the sidebar
        # This provides context about the current store session
        st.sidebar.markdown("---")
        st.sidebar.markdown("**Sucursal**")
        st.sidebar.text(st.session_state.store_name)
        st.sidebar.text(st.session_state.store_address)
        st.sidebar.text(st.session_state.store_location)
        
        # ------------------ Data Synchronization ------------------
        
        # Get stock data just once per session
        # This ensures we have the latest product availability and pricing
        if "is_stock" not in st.session_state:
            try:
                # Set up environment with proper Python path
                env = os.environ.copy()
                env['PYTHONPATH'] = f"{REPO_DIR}:{env.get('PYTHONPATH', '')}"
                
                # Execute stock synchronization script for the current store
                subprocess.run(
                    [sys.executable, PULL_STOCK_PATH, st.session_state.store_id],
                    check=True,
                    env=env
                )
                st.session_state.is_stock = True
            except subprocess.CalledProcessError as e:
                st.error(f"Error al ejecutar el script de stock: {str(e)}")
                st.session_state.is_stock = False
        
        # Get images data just once per session
        # This provides product images and URLs for the chat interface
        if "is_images" not in st.session_state:
            try:
                env = os.environ.copy()
                env['PYTHONPATH'] = f"{REPO_DIR}:{env.get('PYTHONPATH', '')}"
                
                # Execute image synchronization script for the current store
                subprocess.run(
                    [sys.executable, PULL_IMAGES_PATH, st.session_state.store_id],
                    check=True,
                    env=env
                )
                st.session_state.is_images = True
            except subprocess.CalledProcessError as e:
                st.error(f"Error al ejecutar el script de imágenes: {str(e)}")
                st.session_state.is_images = False

        # Get ABM data just once per session
        # This provides product catalog and descriptions for the AI assistant
        if "is_abm" not in st.session_state:
            try:
                env = os.environ.copy()
                env['PYTHONPATH'] = f"{REPO_DIR}:{env.get('PYTHONPATH', '')}"
                
                # Execute ABM synchronization script for the current store
                subprocess.run(
                    [sys.executable, PULL_ABM_PATH, st.session_state.store_id],
                    check=True,
                    env=env
                )
                st.session_state.is_abm = True
            except subprocess.CalledProcessError as e:
                st.error(f"Error al ejecutar el script de ABM: {str(e)}")
                st.session_state.is_abm = False
        
        # ------------------ Real-time Data Updates ------------------
        
        # Initialize stock update timer for periodic updates
        if "last_stock_update" not in st.session_state:
            st.session_state.last_stock_update = time.time()

        # Check if it's time to update stock data
        # Updates occur every hour (configurable via STOCK_UPDATE_INTERVAL)
        if time.time() - st.session_state.last_stock_update >= STOCK_UPDATE_INTERVAL:
            try:
                env = os.environ.copy()
                env['PYTHONPATH'] = f"{REPO_DIR}:{env.get('PYTHONPATH', '')}"
                
                # Execute stock update script
                subprocess.run(
                    [sys.executable, PULL_STOCK_PATH, st.session_state.store_id],
                    check=True,
                    env=env
                )
                st.session_state.last_stock_update = time.time()
            except Exception as e:
                st.error(f"Error actualizando stock: {str(e)}")

        # ------------------ Chat Interface Initialization ------------------
        
        # Initialize chat interface if it doesn't exist
        # This creates the main AI assistant interface
        if "chat" not in st.session_state:
            # Configure chat interface with store-specific settings
            config = ChatConfig(
                title="💬 openfarmAI",
                header_caption=HEADER_CAPTION,
                header_logo_path=HEADER_LOGO_PATH,
                user_avatar_path=AVATAR_USER_PATH,
                bot_avatar_path=AVATAR_BOT_PATH,
                input_placeholder="Escriba su consulta aquí...",
                loading_text="Buscando información..."
            )
            # Create chat instance with API configuration
            st.session_state.chat = Chat(api_key, assistant_id, config)
        
        # Apply chat styling to the interface
        st.html(st.session_state.chat.style.style)

        # Render the main chat interface
        st.session_state.chat.renderChatInterface()

        # Process any pending messages in the queue
        # This handles AI responses and tool calls
        if st.session_state.chat.processQueue(handlers):
            st.rerun()

        # ------------------ Logout and Session Cleanup ------------------
        
        # Add logout button to sidebar
        st.sidebar.markdown("---")
        if st.sidebar.button("Cerrar Sesión", key="logout_button"):
            # Prepare metadata for conversation export
            metadata = {
                'Usuario': st.session_state.username,
                'Sucursal': st.session_state.store_name,
                'Dirección': st.session_state.store_address,
                'Localidad': st.session_state.store_location
            }
            
            # Only export and send if there was actual conversation
            # This prevents empty exports and unnecessary emails
            if len(st.session_state.chat.messages) > 1:
                # Export conversation to PDF with timestamp
                output_path = f"{HISTORY_PATH}/chatbot_{datetime.now().strftime('%Y-%m-%d %H-%M')}.pdf"
                st.session_state.chat.exportConversation(
                    format="pdf", 
                    metadata=metadata, 
                    output_path=output_path
                )

                # Send conversation to email for record keeping
                st.session_state.chat.sendConversationEmail(
                    from_email=EMAIL_FROM, 
                    to_email=EMAIL_TO, 
                    password=EMAIL_PASSWORD, 
                    attachments=[output_path], 
                    metadata=metadata
                )
            
            # Report final prompt count and clear chat state
            st.session_state.chat.clearChat()
            
            # Clear all authentication and session state
            # This ensures a clean logout
            st.session_state.authenticated = False
            st.session_state.username = None
            st.session_state.store_name = None
            st.session_state.store_address = None
            st.session_state.store_location = None
            
            # Remove data synchronization flags
            del st.session_state.is_stock
            del st.session_state.last_stock_update
            
            # Rerun the app to return to login screen
            st.rerun()

# ------------------ Application Entry Point ------------------

if __name__ == "__main__":
    """
    Application entry point.
    
    This block ensures the main function is only called when the script
    is executed directly, not when imported as a module.
    
    The main function handles the complete application lifecycle including
    authentication, data synchronization, chat interface, and session management.
    """
    main()