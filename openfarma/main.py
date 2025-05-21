import os
import sys
import time
import subprocess
import streamlit as st
from datetime import datetime

# Run local or remote, sqlite purpose
RUN_LOCAL = False

if not RUN_LOCAL:
    import pysqlite3
    # Trick to update sqlite
    CHROMA_DB_PATH = os.path.join(os.getcwd(), "openfarma/database/chroma")
    __import__('pysqlite3')
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(CHROMA_DB_PATH, 'db.sqlite3'),
        }
    }

# Get the absolute path to the project directory
REPO_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Check if the src directory exists
src_path = os.path.join(REPO_DIR, 'src')
if not os.path.exists(src_path):
    raise RuntimeError(f"Source directory not found at {src_path}")

# Add the repository directory to the path
if REPO_DIR not in sys.path:
    sys.path.insert(0, REPO_DIR)
    sys.path.insert(0, os.path.join(REPO_DIR, 'src'))
    sys.path.insert(0, os.path.join(REPO_DIR, 'openfarma'))

try:
    from openfarma.src.login import loginPage
    from openfarma.src.params import *
    from openfarma.src.fc import *
    from openfarma.src.chat import Chat, ChatConfig
except ImportError as e:
    raise ImportError(f"Import error: {e}")

# Get API keys from Streamlit secrets
api_key = st.secrets["OPENFARMA_API_KEY"]
assistant_id = st.secrets["OPENFARMA_ASSISTANT_ID"]

# ------------------ Main ------------------

def main():
    # Initialize authentication state
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'username' not in st.session_state:
        st.session_state.username = None

    # Check authentication
    if not st.session_state.authenticated:
        loginPage()
    else:
        # Show store information in sidebar
        st.sidebar.markdown("---")
        st.sidebar.markdown("**Sucursal**")
        st.sidebar.text(st.session_state.store_name)
        st.sidebar.text(st.session_state.store_address)
        st.sidebar.text(st.session_state.store_location)
        
        # Get stock data just once
        if "is_stock" not in st.session_state:
            try:
                env = os.environ.copy()
                env['PYTHONPATH'] = f"{REPO_DIR}:{env.get('PYTHONPATH', '')}"
                subprocess.run(
                    [sys.executable, PULL_STOCK_PATH, st.session_state.store_id],
                    check=True,
                    env=env
                )
                st.session_state.is_stock = True
            except subprocess.CalledProcessError as e:
                st.error(f"Error al ejecutar el script de stock: {str(e)}")
                st.session_state.is_stock = False
        
        # Get images data just once 
        if "is_images" not in st.session_state:
            try:
                env = os.environ.copy()
                env['PYTHONPATH'] = f"{REPO_DIR}:{env.get('PYTHONPATH', '')}"
                subprocess.run(
                    [sys.executable, PULL_IMAGES_PATH, st.session_state.store_id],
                    check=True,
                    env=env
                )
                st.session_state.is_images = True
            except subprocess.CalledProcessError as e:
                st.error(f"Error al ejecutar el script de imágenes: {str(e)}")
                st.session_state.is_images = False

        # Get ABM data just once
        if "is_abm" not in st.session_state:
            try:
                env = os.environ.copy()
                env['PYTHONPATH'] = f"{REPO_DIR}:{env.get('PYTHONPATH', '')}"
                subprocess.run(
                    [sys.executable, PULL_ABM_PATH, st.session_state.store_id],
                    check=True,
                    env=env
                )
                st.session_state.is_abm = True
            except subprocess.CalledProcessError as e:
                st.error(f"Error al ejecutar el script de ABM: {str(e)}")
                st.session_state.is_abm = False
        
        # Initialize stock update timer
        if "last_stock_update" not in st.session_state:
            st.session_state.last_stock_update = time.time()

        # Check if it's time to update stock
        if time.time() - st.session_state.last_stock_update >= STOCK_UPDATE_INTERVAL:
            try:
                env = os.environ.copy()
                env['PYTHONPATH'] = f"{REPO_DIR}:{env.get('PYTHONPATH', '')}"
                subprocess.run(
                    [sys.executable, PULL_STOCK_PATH, st.session_state.store_id],
                    check=True,
                    env=env
                )
                st.session_state.last_stock_update = time.time()
            except Exception as e:
                st.error(f"Error actualizando stock: {str(e)}")

        # Initialize chat if not exists
        if "chat" not in st.session_state:
            config = ChatConfig(
                title="💬 openfarmAI",
                header_caption=HEADER_CAPTION,
                header_logo_path=HEADER_LOGO_PATH,
                user_avatar_path=AVATAR_USER_PATH,
                bot_avatar_path=AVATAR_BOT_PATH,
                input_placeholder="Escriba su consulta aquí...",
                loading_text="Buscando información..."
            )
            st.session_state.chat = Chat(api_key, assistant_id, config)
        st.html(st.session_state.chat.style.style)

        # Render chat interface
        st.session_state.chat.renderChatInterface()

        # Process message queue
        if st.session_state.chat.processQueue(handlers):
            st.rerun()

        # Sidebar logout button
        st.sidebar.markdown("---")
        if st.sidebar.button("Cerrar Sesión", key="logout_button"):
            # Export conversation and report prompts
            metadata = {
                'Usuario': st.session_state.username,
                'Sucursal': st.session_state.store_name,
                'Dirección': st.session_state.store_address,
                'Localidad': st.session_state.store_location
            }
            
            # Only export and send if there was actual conversation
            if len(st.session_state.chat.messages) > 1:
                # Export conversation to PDF
                output_path = f"{HISTORY_PATH}/chatbot_{datetime.now().strftime('%Y-%m-%d %H-%M')}.pdf"
                st.session_state.chat.exportConversation(format="pdf", metadata=metadata, output_path=output_path)

                # Send conversation to email
                st.session_state.chat.sendConversationEmail(
                    from_email=EMAIL_FROM, 
                    to_email=EMAIL_TO, 
                    password=EMAIL_PASSWORD, 
                    attachments=[output_path], 
                    metadata=metadata
                )
            
            # Report final prompt count before clearing
            st.session_state.chat.clearChat()
            
            # Clear authentication and session state
            st.session_state.authenticated = False
            st.session_state.username = None
            st.session_state.store_name = None
            st.session_state.store_address = None
            st.session_state.store_location = None
            
            # Remove keys from session state
            del st.session_state.is_stock
            del st.session_state.last_stock_update
            # Rerun the app
            st.rerun()

if __name__ == "__main__":
    main()