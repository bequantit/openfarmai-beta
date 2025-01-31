import json
import streamlit as st
from openfarma.src.params import *
from src.assistant.assistant import Assistant

# Load openai api key
api_key = st.secrets['OPENFARMA_API_KEY']

# Load function calling definitions
with open(FC_CONFIG_PATH, 'r', encoding='utf-8') as f:
    fc_config = json.load(f)

# Create the OpenAI assistant
assistant = Assistant(api_key)
assistant.importFromFile(ASSISTANT_CONFIG_PATH)
assistant.setResponseFormat("text")

# Add function calling to the assistant
for function in fc_config:
    assistant.addTool("function", function)

# Create the assistant
response = assistant.create()


