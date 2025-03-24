import time
import threading
import sqlite3
from base64 import urlsafe_b64decode
from email import message_from_bytes
from typing import List, Tuple

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from src.gmail.auth import GmailAuth
from src.utils import DB_PATH


class EmailLoader:
    def __init__(self):
        self.auth_service = GmailAuth()
        self._requested_email_ids = set()
        self._new_email_callback = None
        self.worker_thread = None

    def start_monitoring(self):
        self.worker_thread = threading.Thread(
            target=self.get_recent_worker
        )
        self.worker_thread.start()

    def _get_user_creds_from_db(self):
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM auth_tokens")
            users = cursor.fetchall()
        user_creds = []
        for row in users:
            user_id = row[0]
            user_creds.append((user_id, self.auth_service.load_creds(user_id)))
        return user_creds

    def init_emails(self, emails_num: int, max_results: int):
        emails = self.get_emails(emails_num, max_results)
        for email in emails:
            self._requested_email_ids.add(email["id"])
        return emails

    def get_emails(self, emails_num: int, max_results=100) -> List:
        all_emails = []
        user_creds = self._get_user_creds_from_db()
        for user_id, creds in user_creds:
            service = build("gmail", "v1", credentials=creds)
            next_page = None
            for i in range(emails_num // max_results + bool(emails_num % max_results)):
                try:
                    results = service.users().messages().list(userId="me", pageToken=next_page,
                                                              maxResults=max_results).execute()
                    next_page = results.get("nextPageToken")
                    messages = results.get("messages", [])
                    if len(messages) == 0:
                        break
                    for message in messages:
                        msg = service.users().messages().get(userId="me", id=message["id"], format="raw").execute()
                        email_data = self._parse_email(msg["raw"], msg["id"])
                        all_emails.append(email_data)
                except Exception as e:
                    print(f"An error occurred for user {user_id}: {e}")
        return all_emails

    def get_recent(self):
        emails = self.get_emails(5, max_results=5)
        recent = []
        for email in emails:
            if email["id"] in self._requested_email_ids:
                break
            recent.append(email)
            self._requested_email_ids.add(email["id"])
            if self._new_email_callback is not None:
                self._new_email_callback(email)

    def add_email_callback(self, func):
        self._new_email_callback = func

    def get_recent_worker(self):
        while True:
            self.get_recent()
            time.sleep(5)

    def _parse_email(self, raw_email, msg_id: str):
        """Парсит сырое письмо в читаемый формат."""
        msg_bytes = urlsafe_b64decode(raw_email)
        email_message = message_from_bytes(msg_bytes)
        return {
            "id": msg_id,
            "subject": email_message["Subject"],
            "from": email_message["From"],
            "to": email_message["To"],
            "date": email_message["Date"],
            "body": self._get_email_body(email_message),
        }

    def _get_email_body(self, email_message):
        """Извлекает тело письма."""
        if email_message.is_multipart():
            for part in email_message.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    return part.get_payload(decode=True).decode()
        else:
            return email_message.get_payload(decode=True).decode()
