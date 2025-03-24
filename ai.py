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
        
    def add_email(self, email: Dict, embedding: List[float]):
        email_id = str(len(self.email_data))
        self.email_data.append(email)
        
        self.collection.add(
            ids=[email_id],
            embeddings=[embedding],
            metadatas=[{
                "from": email["from"],
                "to": email["to"],
                "date": email["date"],
                "subject": email["subject"]
            }]
        )
        
    def search_by_embedding(self, query_embedding: List[float], k: int = 5) -> List[Dict]:
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k
        )
        
        matched_emails = []
        for i, idx in enumerate(results["ids"][0]):
            email_idx = int(idx)
            email = self.email_data[email_idx].copy()
            email['number'] = email_idx + 1
            matched_emails.append(email)
            
        return matched_emails

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
            self._handle_new_email(email)
    
    def _handle_new_email(self, email: Dict):
        embedding = np.random.rand(self.embedding_dimension).tolist()
        self.vector_db.add_email(email, embedding)
    
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
        query_embedding = np.random.rand(self.embedding_dimension).tolist()
        all_results = self.vector_db.search_by_embedding(query_embedding, k=len(self.vector_db.email_data))
        filtered_results = []
        for result in all_results:
            if criteria_type == "date":
                email_date = self._parse_email_date(result['date'])
                if email_date and email_date == criteria_value:
                    filtered_results.append(result)
            elif criteria_type == "sender" and criteria_value.lower() in result['from'].lower():
                filtered_results.append(result)
        for i, result in enumerate(filtered_results):
            result['number'] = i + 1
            
        return filtered_results
    
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
