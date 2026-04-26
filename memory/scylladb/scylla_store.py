import json
import uuid
from typing import List, Optional
from cassandra.cluster import Cluster
from llama_index.core.storage.chat_store import BaseChatStore
from llama_index.core.llms import ChatMessage, MessageRole

class ScyllaTimeSeriesChatStore(BaseChatStore):
    def __init__(self, contact_points: List[str] = ["127.0.0.1"], keyspace: str = "llamaindex_store"):
        self.cluster = Cluster(contact_points)
        self.session = self.cluster.connect(keyspace)
        
        # Prepare statements for performance and security
        self.insert_stmt = self.session.prepare("""
            INSERT INTO chat_history (session_id, message_id, role, content, additional_kwargs) 
            VALUES (?, ?, ?, ?, ?)
        """)
        self.select_stmt = self.session.prepare("""
            SELECT role, content, additional_kwargs FROM chat_history WHERE session_id = ?
        """)
        self.delete_stmt = self.session.prepare("""
            DELETE FROM chat_history WHERE session_id = ?
        """)

    def add_message(self, key: str, message: ChatMessage) -> None:
        kwargs_json = json.dumps(message.additional_kwargs) if message.additional_kwargs else "{}"
        self.session.execute(self.insert_stmt, (
            key, 
            uuid.uuid1(), # Generates TimeUUID for sorting
            message.role.value, 
            message.content, 
            kwargs_json
        ))

    def get_messages(self, key: str) -> List[ChatMessage]:
        rows = self.session.execute(self.select_stmt, (key,))
        return [
            ChatMessage(
                role=MessageRole(row.role),
                content=row.content,
                additional_kwargs=json.loads(row.additional_kwargs)
            ) for row in rows
        ]

    def set_messages(self, key: str, messages: List[ChatMessage]) -> None:
        self.delete_messages(key)
        for msg in messages:
            self.add_message(key, msg)

    def delete_messages(self, key: str) -> Optional[List[ChatMessage]]:
        msgs = self.get_messages(key)
        self.session.execute(self.delete_stmt, (key,))
        return msgs

    def get_keys(self) -> List[str]:
        # Note: Avoid full table scans in large production datasets
        rows = self.session.execute("SELECT DISTINCT session_id FROM chat_history")
        return [row.session_id for row in rows]
