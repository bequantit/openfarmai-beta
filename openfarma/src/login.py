from __future__ import annotations
import io
import base64
import smtplib
import pandas as pd
import streamlit as st
from PIL import Image
from typing import Optional, Tuple, List
from datetime import datetime
from hashlib import sha256
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from openfarma.src.params import (
    LOGIN_PATH, 
    STORES_PATH, 
    HEADER_LOGO_PATH,
    EMAIL_FROM,
    EMAIL_PASSWORD
)

class Login:
    """
    Class to handle all login related functionality including authentication,
    password recovery and UI rendering.
    
    Attributes:
        HEADER_IMAGE (str): Base64 encoded header image
        USERS_DF (pd.DataFrame): DataFrame containing user credentials
        STORES_DF (pd.DataFrame): DataFrame containing store information
    """
    
    HEADER_IMAGE: Optional[str] = None
    USERS_DF: Optional[pd.DataFrame] = None
    STORES_DF: Optional[pd.DataFrame] = None
    
    def __init__(self) -> None:
        """Initialize login instance and load necessary data."""
        self._loadStaticData()
        self._initializeSessionState()

    @staticmethod
    def _encodeImage(image_path: str) -> str:
        """
        Encode image to base64.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Base64 encoded image string
        """
        try:
            with Image.open(image_path) as image:
                buffered = io.BytesIO()
                image.save(buffered, format="PNG")
                return base64.b64encode(buffered.getvalue()).decode()
        except Exception as e:
            st.error(f"Error encoding image: {str(e)}")
            raise

    def _getUserData(self, username: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Get user credentials and email from database.
        
        Args:
            username: Username to look up
            
        Returns:
            Tuple containing (username, password, email) or (None, None, None) if not found
        """
        try:
            user_data = self.USERS_DF[self.USERS_DF.iloc[:, 1] == username]
            if not user_data.empty:
                return (
                    username,
                    str(user_data.iloc[0, 2]),
                    str(user_data.iloc[0, 3])
                )
            return None, None, None
        except Exception as e:
            st.error(f"Error retrieving user data: {str(e)}")
            return None, None, None

    def _getStoreData(self, store_id: str) -> List[str]:
        """
        Retrieve store data from the stores database.
        
        Args:
            store_id: Store identifier
            
        Returns:
            List containing store details (name, address, location)
        """
        try:
            store_id = str(int(float(store_id)))
            store_data = self.STORES_DF[
                self.STORES_DF.iloc[:, 0] == store_id
            ].iloc[0, 1:].tolist()
            return store_data
        except Exception as e:
            st.error(f"Error retrieving store data: {str(e)}")
            raise

    def _initializeSessionState(self) -> None:
        """Initialize session state variables with default values."""
        session_vars = {
            'recovery_mode': False,
            'authenticated': False,
            'store_id': None,
            'store_name': None,
            'store_address': None,
            'store_location': None,
            'username': None
        }
        
        for var, default in session_vars.items():
            if var not in st.session_state:
                st.session_state[var] = default

    @classmethod
    def _loadStaticData(cls) -> None:
        """Load static data that will be shared across all instances."""
        try:
            if cls.HEADER_IMAGE is None:
                cls.HEADER_IMAGE = cls._encodeImage(HEADER_LOGO_PATH)
            if cls.USERS_DF is None:
                cls.USERS_DF = pd.read_csv(LOGIN_PATH)
            if cls.STORES_DF is None:
                cls._prepareStoresDf()
        except Exception as e:
            st.error(f"Error loading static data: {str(e)}")
            raise

    @classmethod
    def _prepareStoresDf(cls) -> None:
        """Prepare stores dataframe by cleaning and formatting data."""
        try:
            df = pd.read_csv(STORES_PATH)
            df = df.dropna(subset=[df.columns[0]])
            mask = df.iloc[:, 0].astype(str).str.strip() != ''
            df = df[mask].copy()
            df.iloc[:, 0] = pd.to_numeric(df.iloc[:, 0], errors='coerce').fillna(0).astype(int).astype(str)
            cls.STORES_DF = df
        except Exception as e:
            st.error(f"Error preparing stores DataFrame: {str(e)}")
            raise

    def _renderHeader(self) -> None:
        """Render page header with logo."""
        st.markdown(
            f"""
            <img src="data:image/png;base64,{self.HEADER_IMAGE}" 
                 style="width: 350px; display: block; margin: 0 auto;">
            <br><br>
            """, 
            unsafe_allow_html=True
        )

    def _renderLoginForm(self) -> None:
        """Render main login form."""
        usernames = self.USERS_DF.iloc[:, 1].tolist()
        
        with st.form("login_form"):
            self._renderStyles()
            
            left, _ = st.columns(2)
            with left:
                username = st.selectbox("Usuario", usernames, key="username_input")
            
            password = st.text_input(
                "Contraseña",
                type="password",
                help="Haga clic en el ícono del ojo para mostrar/ocultar",
                key="password_input",
                placeholder="Ingrese su contraseña"
            )
            
            left, right = st.columns(2)
            with left:
                submit_button = st.form_submit_button("Iniciar sesión")
                if submit_button:
                    if self._verifyCredentials(username, password):
                        st.rerun()
                    else:
                        st.error("Usuario o contraseña incorrectos")
            
            with right:
                recovery_button = st.form_submit_button("¿Olvidó su contraseña?")
                if recovery_button:
                    st.session_state.recovery_mode = True
                    st.rerun()

    def _renderRecoveryPage(self) -> None:
        """Render password recovery page."""
        with st.form("recovery_form"):
            st.write("### Recuperación de Contraseña")
            usernames = self.USERS_DF.iloc[:, 1].tolist()
            username = st.selectbox("Seleccione su Usuario", usernames, key="recovery_username")
            
            left, right = st.columns(2)
            with left:
                back_button = st.form_submit_button("Volver al Login")
                if back_button:
                    st.session_state.recovery_mode = False
                    st.rerun()
            with right:
                recover_button = st.form_submit_button("Recuperar Contraseña")
                if recover_button:
                    username, password, email = self._getUserData(username)
                    if all((username, password, email)):
                        if self._sendRecoveryEmail(username, password, email):
                            st.success(f"Se enviaron las credenciales a {email}")
                    else:
                        st.error("No se pudo recuperar la información del usuario")

    @staticmethod
    def _renderStyles() -> None:
        """Render CSS styles for the login page."""
        st.markdown("""
            <style>
            [data-testid="stTextInput"] input {
                font-size: 16px !important;
                font-family: 'Arial', sans-serif !important;
                padding: 10px !important;
                border-radius: 5px !important;
            }
            
            div[class*="stTextInput"] label p {
                font-size: 20px !important;
                color: black !important;
                font-weight: bold !important;
            }

            div[data-testid="stSelectbox"] {
                font-size: 16px !important;
                font-family: 'Arial', sans-serif !important;
            }

            div[data-testid="stSelectbox"] > div[role="button"] {
                padding: 10px !important;
                border-radius: 5px !important;
            }

            div[data-testid="stSelectbox"] label p {
                font-size: 20px !important;
                color: black !important;
                font-weight: bold !important;
            }
            </style>
        """, unsafe_allow_html=True)

    def _sendRecoveryEmail(self, username: str, password: str, email: str) -> bool:
        """
        Send recovery email with user credentials.
        
        Args:
            username: Username to recover
            password: Password to recover
            email: Destination email address
            
        Returns:
            Boolean indicating if email was sent successfully
        """
        try:
            email = EMAIL_FROM
            message = MIMEMultipart()
            message['From'] = EMAIL_FROM
            message['To'] = email
            message['Subject'] = f'Recuperación de Contraseña OpenFarmAI'

            body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6;">
                <h2 style="color: #2c3e50;">Recuperación de Credenciales - OpenFarma AI</h2>
                
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px;">
                    <h3 style="color: #2c3e50;">Sus credenciales de acceso:</h3>
                    <ul style="list-style-type: none; padding-left: 0;">
                        <li><strong>Usuario:</strong> {username}</li>
                        <li><strong>Contraseña:</strong> {password}</li>
                    </ul>
                </div>

                <div style="margin-top: 20px;">
                    <p style="color: #666;">
                        Por favor, utilice estas credenciales para iniciar sesión en OpenFarma AI.
                    </p>
                </div>

                <hr style="border: 1px solid #eee; margin: 20px 0;">
                
                <footer style="color: #666; font-size: 12px;">
                    <p>Este es un mensaje automático generado por OpenFarma AI Assistant.</p>
                    <p>Por favor no responda a este correo.</p>
                </footer>
            </body>
            </html>
            """

            message.attach(MIMEText(body, 'html'))

            with smtplib.SMTP('smtp.gmail.com', 587) as session:
                session.starttls()
                session.login(EMAIL_FROM, EMAIL_PASSWORD)
                session.send_message(message)
            
            return True

        except smtplib.SMTPAuthenticationError:
            st.error("Error de autenticación del servidor de correo.")
            return False
        except smtplib.SMTPException as e:
            st.error("Error al enviar el correo electrónico.")
            return False
        except Exception as e:
            st.error("Error inesperado al enviar el correo.")
            return False

    def _setSessionData(self, store_id: str, store_data: List[str], username: str) -> None:
        """
        Set session state data after successful authentication.
        
        Args:
            store_id: Store identifier
            store_data: List of store details
            username: Authenticated username
        """
        try:
            st.session_state.update({
                'store_id': store_id,
                'store_name': store_data[0],
                'store_address': store_data[1],
                'store_location': store_data[2],
                'authenticated': True,
                'username': username
            })
        except Exception as e:
            st.error(f"Error setting session data: {str(e)}")
            raise

    def _verifyCredentials(self, username: str, password: str) -> bool:
        """
        Verify user credentials and set session state if valid.
        
        Args:
            username: Username to verify
            password: Password to verify
            
        Returns:
            Boolean indicating if credentials are valid
        """
        try:
            hashed_password = sha256(str(password).encode()).hexdigest()
            user_data = self.USERS_DF[self.USERS_DF.iloc[:, 1] == username]
            
            if not user_data.empty:
                stored_hash = sha256(str(user_data.iloc[0, 2]).encode()).hexdigest()
                
                if hashed_password == stored_hash:
                    store_id = str(int(float(user_data.iloc[0, 0])))
                    store_data = self._getStoreData(store_id)
                    self._setSessionData(store_id, store_data, username)
                    return True
            
            return False
        except Exception as e:
            st.error(f"Error verifying credentials: {str(e)}")
            return False

    def render(self) -> None:
        """Main method to render the login page."""
        self._renderHeader()
        
        if st.session_state.recovery_mode:
            self._renderRecoveryPage()
        else:
            self._renderLoginForm()


def loginPage() -> None:
    """Legacy function to maintain backwards compatibility."""
    login = Login()
    login.render()