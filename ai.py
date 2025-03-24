import chromadb
import numpy as np
from typing import List, Dict, Optional
import json
import os
import datetime
from src.gmail.emails_loading import EmailLoader

class EmailVectorDatabase:
    def __init__(self, collection_name: str = "emails"):
        self.client = chromadb.Client()
        self.collection = self.client.get_or_create_collection(collection_name)
        self.email_data = []
        
    def add_email(self, email: Dict):
        email_id = str(len(self.email_data))
        self.email_data.append(email)
        if not email["body"]:
            return
        self.collection.add(
            ids=[email_id],
            metadatas=[{
                "from": email["from"],
                "to": email["to"],
                "date": email["date"],
                "subject": email["subject"]
            }],
            documents=[email["body"]]
        )
        
    def search_by_embedding(self, query_params: Dict, k: int = 5) -> chromadb.QueryResult:
        results = self.collection.query(
            query_texts=[""],
            where=query_params,
            n_results=k
        )
        return results

class EmailBridge:
    def __init__(self, embedding_dimension: int = 768):
        self.email_loader = EmailLoader()
        self.vector_db = EmailVectorDatabase()
        self.embedding_dimension = embedding_dimension
        
    def setup(self):
        self.email_loader.add_email_callback(self._handle_new_email)
        self.email_loader.start_monitoring()
        initial_emails = self.email_loader.init_emails(50, 50)
        for email in initial_emails:
            print(email)
            self._handle_new_email(email)
    
    def _handle_new_email(self, email: Dict):
        self.vector_db.add_email(email)
    
    def _parse_email_date(self, date_str: str) -> Optional[str]:
        """Преобразует строку даты в формат YYYY-MM-DD."""
        try:
            for fmt in ["%a, %d %b %Y %H:%M:%S %z", "%d %b %Y %H:%M:%S %z"]:
                try:
                    dt = datetime.datetime.strptime(date_str, fmt)
                    return dt.strftime("%Y-%m-%d")
                except ValueError:
                    continue
            return None
        except Exception:
            return None

    def get_emails_by_criteria(self, criteria_type: str, criteria_value: str, top_k: int = 5) -> List[Dict]:
        meta_filter = {criteria_type: {"$eq": criteria_value}}
        emails = self.vector_db.search_by_embedding(meta_filter, top_k)
        print(emails)
        return emails

    def get_email_summaries(self, criteria_type: str, criteria_value: str) -> List[Dict]:
        """Получает список писем с номерами и темами для отображения."""
        emails = self.get_emails_by_criteria(criteria_type, criteria_value)
        
        summaries = []
        for email in emails:
            summaries.append({
                "number": email["number"],
                "subject": email["subject"] or "(No Subject)"
            })
        
        return summaries
    
    def get_email_by_number(self, number: int) -> Optional[Dict]:
        """Получает полное содержимое письма по его номеру."""
        if 0 < number <= len(self.vector_db.email_data):
            return self.vector_db.email_data[number - 1]
        return None
