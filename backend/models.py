from sqlalchemy import Column, String, Boolean, Integer, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
import uuid

Base = declarative_base()

class Name(Base):
    __tablename__ = 'names'
    id = Column(Integer, primary_key=True)
    name_text = Column(String(100), unique=True, nullable=False)
    is_picked = Column(Boolean, default=False)
    picked_at = Column(TIMESTAMP)
    pick_order = Column(Integer)

class Ticket(Base):
    __tablename__ = 'tickets'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    grid = Column(JSONB, nullable=False)
    player_name = Column(String(100))
    is_assigned = Column(Boolean, default=False)
    status = Column(String(20), default='active')
    claimed_at = Column(TIMESTAMP)
    assigned_at = Column(TIMESTAMP)
    created_at = Column(TIMESTAMP)

class GameState(Base):
    __tablename__ = 'game_state'
    key = Column(String(50), primary_key=True)
    value = Column(JSONB, nullable=False)
    updated_at = Column(TIMESTAMP)

class ClaimQueue(Base):
    __tablename__ = 'claim_queue'
    id = Column(Integer, primary_key=True)
    ticket_id = Column(UUID(as_uuid=True), ForeignKey('tickets.id'))
    claimed_at = Column(TIMESTAMP)
    status = Column(String(20), default='pending')
    verified_by = Column(String(50))
    verified_at = Column(TIMESTAMP)
    is_valid = Column(Boolean, default=False)