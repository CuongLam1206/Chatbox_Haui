import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import json
import os

from core.config import (
    GOOGLE_SHEET_ID,
    GOOGLE_SERVICE_ACCOUNT_EMAIL,
    GOOGLE_PRIVATE_KEY,
    GOOGLE_LOG_SHEET_NAME
)

class GoogleSheetsLogger:
    """
    Handler for logging chatbot interactions to a Google Sheet.
    """
    
    def __init__(self):
        self.sheet_id = GOOGLE_SHEET_ID
        self.service_account_email = GOOGLE_SERVICE_ACCOUNT_EMAIL
        self.private_key = GOOGLE_PRIVATE_KEY
        self.sheet_name = GOOGLE_LOG_SHEET_NAME
        
        self.gc = None
        self.worksheet = None
        
        if not all([self.sheet_id, self.service_account_email, self.private_key]):
            print("[GoogleSheets] Missing credentials. Logging disabled.")
            return

        try:
            # Handle potential escaped newlines in private key from .env
            formatted_key = self.private_key.replace('\\n', '\n') if self.private_key else ""
            
            # Create credentials info dict
            info = {
                "type": "service_account",
                "project_id": "hwlab-491405", # Derived from email domain or project
                "private_key_id": "",
                "private_key": formatted_key,
                "client_email": self.service_account_email,
                "client_id": "",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/{self.service_account_email}"
            }
            
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            
            credentials = Credentials.from_service_account_info(info, scopes=scopes)
            self.gc = gspread.authorize(credentials)
            
            # Open the spreadsheet and get/create the worksheet
            spreadsheet = self.gc.open_by_key(self.sheet_id)
            
            try:
                self.worksheet = spreadsheet.worksheet(self.sheet_name)
            except gspread.exceptions.WorksheetNotFound:
                # Create a new tab if it doesn't exist
                self.worksheet = spreadsheet.add_worksheet(title=self.sheet_name, rows="1000", cols="8")
                # Add Header
                self.worksheet.append_row([
                    "Timestamp (VN)", 
                    "User Name", 
                    "Facebook ID", 
                    "Question", 
                    "Answer", 
                    "Sources", 
                    "Relevance Score",
                    "Status"
                ])
                # Format header
                self.worksheet.format("A1:H1", {
                    "textFormat": {"bold": True},
                    "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9}
                })
            
            print(f"✓ Connected to Google Sheet: {self.sheet_name}")
            
        except Exception as e:
            print(f"⚠ Failed to connect to Google Sheets: {e}")
            self.gc = None

    def append_log(self, user_name, user_id, question, answer, sources=None, relevance=0.0):
        """
        Append a log entry to the worksheet.
        """
        if not self.worksheet:
            return False
            
        try:
            # Vietnam Time (GMT+7)
            import pytz
            vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')
            now_vn = datetime.now(vn_tz).strftime('%Y-%m-%d %H:%M:%S')
            
            sources_str = ", ".join(sources) if sources else ""
            
            row = [
                now_vn,
                user_name,
                user_id,
                question,
                answer,
                sources_str,
                f"{relevance:.2%}",
                "Success"
            ]
            
            self.worksheet.append_row(row)
            return True
        except Exception as e:
            print(f"⚠ Error appending log to Google Sheets: {e}")
            return False
