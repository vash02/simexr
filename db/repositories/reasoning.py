
from pathlib import Path
from typing import List
import json
from ..config.database import DatabaseConfig

class ReasoningRepository:
    def __init__(self, db_config: DatabaseConfig = None):
        self.db_config = db_config or DatabaseConfig()

    def store_report(self, model_id: str, question: str, answer, image_paths: List[str]) -> None:
        """
        Insert a reasoning report into the `reasoning_agent` table.
        
        Args:
            model_id: The ID of the model
            question: The question asked
            answer: The answer (can be string or dict - if dict, will extract 'answer' key or serialize)
            image_paths: List of image paths
        """
        # Handle both string and dict answers
        if isinstance(answer, dict):
            # If it's a dict, try to extract the 'answer' key, otherwise serialize the whole dict
            answer_text = answer.get('answer', json.dumps(answer, ensure_ascii=False))
        else:
            answer_text = str(answer)
            
        with self.db_config.get_sqlite_connection() as conn:
            conn.execute("""
                INSERT INTO reasoning_agent (model_id, question, answer, images)
                VALUES (?, ?, ?, ?)
            """, (
                model_id,
                question,
                answer_text,
                json.dumps(image_paths, ensure_ascii=False),
            ))