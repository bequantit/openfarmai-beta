import json
import gspread
import streamlit as st
from datetime import datetime, timedelta
from typing import Dict
from google.oauth2.service_account import Credentials
from openfarma.src.params import (
    PROMPT_TRACKING_SHEET_ID,
    PROMPT_TRACKING_INTERVAL_MINUTES,
    CREDENTIALS_PATH,
    SCOPES
)

class PromptTracker:
    """
    Tracks and reports prompt usage per session.
    """
    
    def __init__(self) -> None:
        """Initialize the prompt tracker."""
        self._initializeSessionState()
        
    def _initializeSessionState(self) -> None:
        """Initialize session state variables for tracking."""
        if 'prompt_count' not in st.session_state:
            st.session_state.prompt_count = 0
        if 'last_prompt_report' not in st.session_state:
            st.session_state.last_prompt_report = datetime.now()
            
    def incrementPromptCount(self) -> None:
        """Increment the prompt counter and check if reporting is needed."""
        st.session_state.prompt_count += 1
        self._checkAndReport()
        
    def _checkAndReport(self) -> None:
        """Check if it's time to report based on time interval."""
        current_time = datetime.now()
        time_elapsed = current_time - st.session_state.last_prompt_report
        
        if time_elapsed >= timedelta(minutes=PROMPT_TRACKING_INTERVAL_MINUTES):
            self.reportPrompts()
            
    def reportPrompts(self) -> None:
        """Report current prompt count to Google Sheet and reset counter."""
        if st.session_state.prompt_count > 0:
            try:
                data = {
                    'store_id': st.session_state.store_id,
                    'store_name': st.session_state.store_name,
                    'since_datetime': st.session_state.last_prompt_report.strftime('%Y-%m-%d %H:%M:%S'),
                    'to_datetime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'number_of_prompts': st.session_state.prompt_count
                }
                
                self._saveToGoogleSheet(data)
                
                # Reset counter and update last report time
                st.session_state.prompt_count = 0
                st.session_state.last_prompt_report = datetime.now()
                
            except Exception as e:
                st.error(f"Error al reportar prompts: {str(e)}")
    
    def _saveToGoogleSheet(self, data: Dict) -> None:
        """
        Save prompt tracking data to Google Sheet.
        
        Args:
            data: Dictionary containing tracking data
        """
        try:
            # Authenticate with service account
            credentials = json.loads(st.secrets["credentials"]["json"])
            with open(CREDENTIALS_PATH, "w") as json_file:
                json.dump(credentials, json_file, indent=4)
            credentials = Credentials.from_service_account_file(CREDENTIALS_PATH, scopes=SCOPES)

            # Create gspread client with credentials
            gc = gspread.authorize(credentials)
            
            # Open the sheet
            sheet = gc.open_by_key(PROMPT_TRACKING_SHEET_ID).sheet1
            
            # Append new row
            sheet.append_row([
                data['store_id'],
                data['store_name'],
                data['since_datetime'],
                data['to_datetime'],
                data['number_of_prompts']
            ])
            
        except Exception as e:
            raise Exception(f"Error saving to Google Sheet: {str(e)}")