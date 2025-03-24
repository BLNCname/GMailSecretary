import sqlite3
from typing import Optional
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from urllib.parse import urlparse, parse_qs

from src.utils import DB_PATH

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
PATH_TO_SECRETS = "configs/client_secrets.json"


class GmailAuth:
    """
    Auth mechanism:
    1. get_auth_url
    2. input(auth_code)
    3. fetch_token(auth_code)
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self.active_flows = {}

    def _save_token_to_db(self, user_id: str, token: str):
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO auth_tokens (user_id, token)
                VALUES (?, ?)
            """, (user_id, token))
            conn.commit()

    def _load_token_from_db(self, user_id: str) -> Optional[str]:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT token FROM auth_tokens WHERE user_id = ?", (user_id,))
            result = json.loads(cursor.fetchone()[0])
            return result if result else None

    @staticmethod
    def get_creds_from_token(token: str) -> Credentials:
        creds = Credentials.from_authorized_user_info(json.loads(token), SCOPES)
        return creds

    def get_auth_url(self, user_id: str):
        flow = InstalledAppFlow.from_client_secrets_file(PATH_TO_SECRETS,
                                                         SCOPES,
                                                         redirect_uri="http://localhost:8080/")
        self.active_flows[user_id] = flow
        authorization_url, _ = flow.authorization_url(
            access_type="offline",  # Запрашиваем offline-доступ
            prompt="consent",  # Запрашиваем согласие пользователя
            include_granted_scopes="true"
        )
        return authorization_url

    def fetch_token(self, user_id: str, auth_code: str):
        parsed_url = urlparse(auth_code)
        params = parse_qs(parsed_url.query)
        auth_code = params.get("code")[0]
        flow = self.active_flows[user_id]
        flow.fetch_token(code=auth_code)
        creds = flow.credentials
        self.active_flows.pop(user_id)
        self._save_token_to_db(user_id, str(creds.to_json()))
        return creds

    def load_creds(self, user_id: str) -> Optional[Credentials]:
        creds = None
        token = self._load_token_from_db(user_id)
        if token:
            creds = Credentials.from_authorized_user_info(token, SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                self._save_token_to_db(user_id, str(creds.to_json()))
        return creds
