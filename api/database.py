"""
Database module for Maestro Builder API
Handles SQLite operations for chat sessions and YAML files
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import uuid

class Database:
    def __init__(self, db_path: str = "storage/maestro_builder.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create chat_sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    message_count INTEGER DEFAULT 0
                )
            """)
            
            # Create messages table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (chat_id) REFERENCES chat_sessions (id) ON DELETE CASCADE
                )
            """)
            
            # Create yaml_files table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS yaml_files (
                    chat_id TEXT NOT NULL,
                    file_name TEXT NOT NULL,
                    content TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (chat_id, file_name),
                    FOREIGN KEY (chat_id) REFERENCES chat_sessions (id) ON DELETE CASCADE
                )
            """)
            
            # Create indexes for better performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_chat_id ON messages (chat_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages (timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_yaml_files_chat_id ON yaml_files (chat_id)")
            
            conn.commit()
    
    def create_chat_session(self, chat_id: Optional[str] = None, name: Optional[str] = None) -> str:
        """Create a new chat session"""
        if not chat_id:
            chat_id = str(uuid.uuid4())
        
        if not name:
            name = f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO chat_sessions (id, name, created_at, updated_at, message_count)
                VALUES (?, ?, ?, ?, 0)
            """, (chat_id, name, datetime.now(), datetime.now()))
            conn.commit()
        
        return chat_id
    
    def get_chat_session(self, chat_id: str) -> Optional[Dict[str, Any]]:
        """Get a chat session by ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, created_at, updated_at, message_count
                FROM chat_sessions
                WHERE id = ?
            """, (chat_id,))
            
            row = cursor.fetchone()
            if row:
                return {
                    "id": row[0],
                    "name": row[1],
                    "created_at": row[2],
                    "updated_at": row[3],
                    "message_count": row[4]
                }
        return None
    
    def get_all_chat_sessions(self) -> List[Dict[str, Any]]:
        """Get all chat sessions"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, created_at, updated_at, message_count
                FROM chat_sessions
                ORDER BY updated_at DESC
            """)
            
            sessions = []
            for row in cursor.fetchall():
                sessions.append({
                    "id": row[0],
                    "name": row[1],
                    "created_at": row[2],
                    "updated_at": row[3],
                    "message_count": row[4]
                })
            return sessions
    
    def add_message(self, chat_id: str, role: str, content: str) -> int:
        """Add a message to a chat session"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO messages (chat_id, role, content, timestamp)
                VALUES (?, ?, ?, ?)
            """, (chat_id, role, content, datetime.now()))
            
            # Update message count and updated_at in chat_sessions
            cursor.execute("""
                UPDATE chat_sessions
                SET message_count = message_count + 1, updated_at = ?
                WHERE id = ?
            """, (datetime.now(), chat_id))
            
            conn.commit()
            return cursor.lastrowid
    
    def get_messages(self, chat_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get messages for a chat session"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT id, role, content, timestamp
                FROM messages
                WHERE chat_id = ?
                ORDER BY timestamp ASC
            """
            
            if limit:
                query += f" LIMIT {limit}"
            
            cursor.execute(query, (chat_id,))
            
            messages = []
            for row in cursor.fetchall():
                messages.append({
                    "id": row[0],
                    "role": row[1],
                    "content": row[2],
                    "timestamp": row[3]
                })
            return messages
    
    def update_yaml_files(self, chat_id: str, yaml_files: Dict[str, str]):
        """Update YAML files for a chat session"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            for file_name, content in yaml_files.items():
                cursor.execute("""
                    INSERT OR REPLACE INTO yaml_files (chat_id, file_name, content, updated_at)
                    VALUES (?, ?, ?, ?)
                """, (chat_id, file_name, content, datetime.now()))
            
            conn.commit()
    
    def get_yaml_files(self, chat_id: str) -> Dict[str, str]:
        """Get YAML files for a chat session"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT file_name, content
                FROM yaml_files
                WHERE chat_id = ?
            """, (chat_id,))
            
            yaml_files = {}
            for row in cursor.fetchall():
                yaml_files[row[0]] = row[1]
            
            return yaml_files
    
    def delete_chat_session(self, chat_id: str) -> bool:
        """Delete a chat session and all associated data"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM chat_sessions WHERE id = ?", (chat_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def delete_all_chat_sessions(self) -> bool:
        """Delete all chat sessions and all associated data"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM chat_sessions")
            conn.commit()
            return True
    
    def get_chat_summary(self, chat_id: str) -> Optional[Dict[str, Any]]:
        """Get a summary of a chat session including last message"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT cs.id, cs.name, cs.created_at, cs.updated_at, cs.message_count,
                       m.content as last_message
                FROM chat_sessions cs
                LEFT JOIN messages m ON m.chat_id = cs.id
                WHERE cs.id = ?
                ORDER BY m.timestamp DESC
                LIMIT 1
            """, (chat_id,))
            
            row = cursor.fetchone()
            if row:
                return {
                    "id": row[0],
                    "name": row[1],
                    "created_at": row[2],
                    "updated_at": row[3],
                    "message_count": row[4],
                    "last_message": row[5] if row[5] else ""
                }
        return None 