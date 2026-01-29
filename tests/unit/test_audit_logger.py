import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models.database import Base, AuditLog
from src.services.audit_logger import AuditLogger

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()

def test_log_action(db_session):
    logger = AuditLogger(db_session)
    customer_id = "test-customer-id"
    session_id = "test-session-id"
    
    logger.log(
        action="order_created",
        customer_id=customer_id,
        session_id=session_id,
        details={"order_id": "test-order-id"},
        severity="info"
    )
    
    logs = db_session.query(AuditLog).all()
    assert len(logs) == 1
    assert logs[0].action == "order_created"
    assert logs[0].customer_id == customer_id

def test_log_warning(db_session):
    logger = AuditLogger(db_session)
    
    logger.log(
        action="low_confidence",
        details={"confidence": 0.5},
        severity="warning"
    )
    
    logs = db_session.query(AuditLog).filter(AuditLog.severity == "warning").all()
    assert len(logs) == 1
