import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class SessionManager:
    """
    Manages in-memory user sessions.
    For production, this would be replaced by a persistent store (database, Redis).
    """
    def __init__(self):
        self._sessions: Dict[str, Dict[str, Any]] = {}
        logger.info("SessionManager initialized (in-memory).")

    def create_session(self, session_id: str, initial_data: Dict[str, Any]) -> None:
        """Creates a new session."""
        if session_id in self._sessions:
            logger.warning(f"Session ID {session_id} already exists. Overwriting.")
        self._sessions[session_id] = initial_data
        logger.debug(f"Session {session_id} created.")

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves session data by ID."""
        session_data = self._sessions.get(session_id)
        if session_data is None:
            logger.debug(f"Session {session_id} not found.")
        return session_data

    def update_session(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """Updates session data."""
        if session_id not in self._sessions:
            logger.warning(f"Attempted to update non-existent session {session_id}.")
            return False
        self._sessions[session_id].update(updates)
        logger.debug(f"Session {session_id} updated.")
        return True

    def delete_session(self, session_id: str) -> bool:
        """Deletes a session."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            logger.debug(f"Session {session_id} deleted.")
            return True
        logger.warning(f"Attempted to delete non-existent session {session_id}.")
        return False

    def list_sessions(self) -> List[str]:
        """Lists all active session IDs."""
        return list(self._sessions.keys())