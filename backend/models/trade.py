"""
Trade model for SQLAlchemy ORM.
Stores trade history with entry/exit prices, P&L, and status.
"""
from sqlalchemy import Column, Integer, String, Numeric, DateTime, Text
from datetime import datetime
from ..database import Base


class Trade(Base):
    """Trade data model."""
    
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True, index=True)
    strategy = Column(String(50), nullable=False)
    symbol = Column(String(20), nullable=False, index=True)
    side = Column(String(10), nullable=False)  # 'long' or 'short'
    
    # Prices
    entry_price = Column(Numeric(20, 8), nullable=False)
    exit_price = Column(Numeric(20, 8), nullable=True)
    qty = Column(Numeric(20, 8), nullable=False)
    
    # Risk management
    stop_loss = Column(Numeric(20, 8), nullable=False)
    take_profit = Column(Numeric(20, 8), nullable=False)
    
    # P&L
    pnl = Column(Numeric(20, 8), nullable=True)
    pnl_pct = Column(Numeric(10, 4), nullable=True)
    exit_reason = Column(String(50), nullable=True)
    
    # Timestamps
    opened_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    closed_at = Column(DateTime, nullable=True, index=True)
    
    # Status
    status = Column(String(20), default="open", nullable=False, index=True)  # 'open', 'closed', 'cancelled'
    notes = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<Trade(id={self.id}, symbol={self.symbol}, side={self.side}, pnl={self.pnl})>"
