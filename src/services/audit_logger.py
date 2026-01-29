from sqlalchemy.orm import Session
from src.models.database import AuditLog
from datetime import datetime
import json
from typing import Optional, Dict

class AuditLogger:
    def __init__(self, db: Session):
        self.db = db
    
    def log(
        self,
        action: str,
        customer_id: Optional[str] = None,
        session_id: Optional[str] = None,
        details: Dict = None,
        performed_by: str = "system",
        severity: str = "info"
    ):
        log_entry = AuditLog(
            action=action,
            customer_id=str(customer_id) if customer_id else None,
            session_id=str(session_id) if session_id else None,
            details=json.dumps(details or {}),
            performed_by=performed_by,
            severity=severity,
            timestamp=datetime.utcnow()
        )
        self.db.add(log_entry)
        self.db.commit()
