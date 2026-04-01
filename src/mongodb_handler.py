"""
MongoDB Conversation Management
"""
from pymongo import MongoClient
from datetime import datetime
from typing import List, Dict, Optional
import uuid

from core.config import MONGO_URI, MONGO_DB_NAME, MONGO_COLLECTION


class ConversationManager:
    """
    Manage conversation history in MongoDB
    """
    
    def __init__(self, mongo_uri: str = MONGO_URI, db_name: str = MONGO_DB_NAME):
        """
        Initialize MongoDB connection
        
        Args:
            mongo_uri: MongoDB connection URI
            db_name: Database name
        """
        print(f"Connecting to MongoDB: {db_name}")
        
        try:
            self.client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
            # Test connection
            self.client.server_info()
            
            self.db = self.client[db_name]
            self.conversations = self.db[MONGO_COLLECTION]
            
            # Create index on session_id for faster queries
            self.conversations.create_index("session_id")
            
            print("✓ MongoDB connected successfully")
        except Exception as e:
            print(f"⚠ MongoDB connection failed: {e}")
            print("  Will continue without conversation persistence")
            self.client = None
    
    def create_session(self, user_id: Optional[str] = None) -> str:
        """
        Create a new conversation session
        
        Args:
            user_id: Optional user identifier
            
        Returns:
            Session ID (UUID)
        """
        if not self.client:
            return str(uuid.uuid4())
        
        session_id = str(uuid.uuid4())
        
        self.conversations.insert_one({
            "session_id": session_id,
            "user_id": user_id,
            "messages": [],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })
        
        print(f"✓ Created session: {session_id}")
        return session_id
    
    def add_message(
        self, 
        session_id: str, 
        role: str, 
        content: str, 
        sources: Optional[List[str]] = None,
        metadata: Optional[Dict] = None
    ):
        """
        Add a message to conversation history
        
        Args:
            session_id: Session identifier
            role: 'user' or 'assistant'
            content: Message content
            sources: List of source document references
            metadata: Additional metadata
        """
        if not self.client:
            return
        
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow()
        }
        
        if sources:
            message["sources"] = sources
        
        if metadata:
            message["metadata"] = metadata
        
        self.conversations.update_one(
            {"session_id": session_id},
            {
                "$push": {"messages": message},
                "$set": {"updated_at": datetime.utcnow()}
            },
            upsert=True 
        )
    
    def get_history(self, session_id: str, limit: int = 10) -> List[Dict]:
        """
        Retrieve conversation history
        
        Args:
            session_id: Session identifier
            limit: Maximum number of messages to retrieve
            
        Returns:
            List of messages
        """
        if not self.client:
            return []
        
        conv = self.conversations.find_one({"session_id": session_id})
        
        if conv and "messages" in conv:
            if limit:
                return conv["messages"][-limit:]
            return conv["messages"]
        
        return []
    
    def get_session_info(self, session_id: str) -> Optional[Dict]:
        """
        Get session information
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session document or None
        """
        if not self.client:
            return None
        
        return self.conversations.find_one(
            {"session_id": session_id},
            {"_id": 0}  # Exclude MongoDB _id
        )
    
    def delete_session(self, session_id: str):
        """
        Delete a conversation session
        
        Args:
            session_id: Session identifier
        """
        if not self.client:
            return
        
        result = self.conversations.delete_one({"session_id": session_id})
        print(f"✓ Deleted session: {session_id} ({result.deleted_count} documents)")
    
    def list_sessions(self, user_id: Optional[str] = None, limit: int = 20) -> List[Dict]:
        """
        List conversation sessions
        
        Args:
            user_id: Filter by user ID
            limit: Maximum number of sessions
            
        Returns:
            List of session summaries
        """
        if not self.client:
            return []
        
        query = {"user_id": user_id} if user_id else {}
        
        sessions = self.conversations.find(
            query,
            {"session_id": 1, "created_at": 1, "updated_at": 1, "messages": {"$slice": 1}}
        ).sort("updated_at", -1).limit(limit)
        
        return list(sessions)
