import io, base64
import pandas as pd
import streamlit as st
from PIL import Image
from hashlib import sha256
from openfarma.src.params import LOGIN_PATH, STORES_PATH, HEADER_LOGO_PATH

def encodeImage(image_path: str) -> str:
    """Encode image to base64"""
    image = Image.open(image_path)
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

def getStoreData(id: str) -> list:
    """
    Retrieves store data from the database based on the store ID.
    """
    id = str(int(float(id)))
    df = pd.read_csv(STORES_PATH)
    df = df.dropna(subset=[df.columns[0]])
    df = df[df.iloc[:, 0] != '']
    df.iloc[:, 0] = df.iloc[:, 0].astype(float).astype(int).astype(str)
    store_data = df[df.iloc[:, 0] == id].to_dict(orient='records')[0]
    store_data = list(store_data.values())
    return store_data[1:]

def verifyCredentials(username: str, password: str) -> bool:
    """
    Verifies user credentials against stored values in the login database.
    
    Args:
        username (str): The username to verify
        password (str): The password to verify
        
    Returns:
        bool: True if credentials are valid, False otherwise

    Raises:
        Exception: If there is an error verifying the credentials
        
    Note:
        The login database contains the following columns:
        - ID sucursal: Branch office ID
        - Usuario: Username 
        - Contraseña: Password
    """
    try:
        df = pd.read_csv(LOGIN_PATH)
        hashed_password = sha256(str(password).encode()).hexdigest()
        user_row = df[df.iloc[:, 1] == username]
        
        if not user_row.empty:
            stored_password = str(user_row.iloc[0, 2])
            stored_hash = sha256(stored_password.encode()).hexdigest()

            if hashed_password == stored_hash:
                store_id = str(int(float(str(user_row.iloc[0, 0]))))
                store_data = getStoreData(store_id)
                st.session_state.store_id = store_id
                st.session_state.store_name = store_data[0]
                st.session_state.store_address = store_data[1]
                st.session_state.store_location = store_data[2]
                return True
        
        return False
    except Exception as e:
        st.error(f"Error al verificar credenciales: {str(e)}")
        return False

def loginPage():
    """
    Displays a login page for the user to enter their credentials.

    1. Displays the login interface with:
       - Header logo image
       - Username input field 
       - Password input field with show/hide option
       - Login submit button

    2. When submit button is clicked:
       - Validates credentials against login database
       - If valid:
         - Sets session state variables (store_id, name, address, location)
         - Grants access to the application
       - If invalid:
         - Shows error message
         - Keeps user on login page

    3. Styling:
       - Custom CSS for input fields and labels
       - Centered layout with responsive columns
       - Professional look and feel

    Note: 
    Currently using hardcoded credentials for testing (Iriondo/Iriondo)
    instead of database verification.
    """
    header_logo = encodeImage(HEADER_LOGO_PATH)
    st.markdown(f"""<img src="data:image/jpeg;base64,{header_logo}" class="header-image" style="width: 400px;">""", 
                unsafe_allow_html=True)
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    with st.form("login_form"):
        
        # Style for login panel
        st.write("""
            <style>
            /* Style for input fields */
            [data-testid="stTextInput"] input {
                font-size: 16px !important;
                font-family: 'Arial', sans-serif !important;
                padding: 10px !important;
                border-radius: 5px !important;
            }
            
            /* Style for labels */
            div[class*="stTextInput"] label p {
                font-size: 20px !important;
                color: black !important;
                font-weight: bold !important;
            }
            </style>
            """, unsafe_allow_html=True)
        
        # Username input
        username = st.text_input("Usuario", 
                                 key="username_input", 
                                 placeholder="Ingrese su usuario")
        
        # Password input
        password = st.text_input("Contraseña",
                               type="password", 
                               help="Haga clic en el ícono del ojo para mostrar/ocultar",
                               key="password_input",
                               placeholder="Ingrese su contraseña")
        
        # Enter button
        _, center, _ = st.columns([1,1,1], gap="large", vertical_alignment="center")
        with center:
            submit_button = st.form_submit_button("INGRESAR")
        
        if submit_button:
            if verifyCredentials(username, password):
            #if username == "Iriondo" and password == "Iriondo":
                # Manually set the San Fernando's store data
                #st.session_state.store_id = "20"
                store_data = getStoreData(st.session_state.store_id)
                st.session_state.store_name = store_data[0]
                st.session_state.store_address = store_data[1]
                st.session_state.store_location = store_data[2]
                st.session_state.authenticated = True
                st.session_state.username = username
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos")
