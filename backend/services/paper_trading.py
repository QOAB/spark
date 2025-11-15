"""
Paper Trading Engine.
Simulates trading without real money, tracks equity and positions.
"""
from typing import Dict, List, Optional
from datetime import datetime
from ..config import settings


class PaperTradingEngine:
    """Paper trading simulation engine."""
    
    def __init__(self, initial_capital: float = None):
        """Initialize paper trading engine."""
        self.initial_capital = initial_capital or settings.INITIAL_CAPITAL
        self.equity = self.initial_capital
        self.available = self.initial_capital
        self.positions: Dict[str, Dict] = {}
        self.daily_pnl = 0.0
        self.daily_loss_limit = settings.DAILY_LOSS_LIMIT
    
    def calculate_position_size(
        self,
        entry_price: float,
        stop_price: float,
        risk_percent: float = None
    ) -> float:
        """
        Calculate position size based on risk management rules.
        
        Args:
            entry_price: Entry price for the position
            stop_price: Stop loss price
            risk_percent: Risk per trade (default from settings)
        
        Returns:
            Position size in base currency (e.g., BTC amount for BTC/USDT)
        """
        risk_pct = risk_percent or settings.RISK_PER_TRADE
        
        # Calculate risk amount in quote currency (USDT)
        risk_amount = self.equity * (risk_pct / 100.0)
        
        # Calculate stop distance
        stop_distance = abs(entry_price - stop_price)
        
        # Calculate position size: risk_amount / stop_distance
        if stop_distance == 0:
            return 0.0
        
        qty = risk_amount / stop_distance
        
        # Ensure we have enough capital
        position_cost = qty * entry_price
        if position_cost > self.available:
            qty = self.available / entry_price
        
        return qty
    
    def open_position(
        self,
        symbol: str,
        side: str,
        entry_price: float,
        qty: float,
        stop_loss: float,
        take_profit: float
    ) -> Dict:
        """
        Open a new position.
        
        Args:
            symbol: Trading pair (e.g., 'BTC/USDT')
            side: 'long' or 'short'
            entry_price: Entry price
            qty: Position size
            stop_loss: Stop loss price
            take_profit: Take profit price
        
        Returns:
            Position dict with details
        """
        # Check max positions limit
        if len(self.positions) >= settings.MAX_OPEN_POSITIONS:
            raise Exception(f"Maximum {settings.MAX_OPEN_POSITIONS} positions allowed")
        
        # Check daily loss limit
        daily_loss_pct = (self.daily_pnl / self.initial_capital) * 100
        if daily_loss_pct <= -self.daily_loss_limit:
            raise Exception(f"Daily loss limit reached: {daily_loss_pct:.2f}%")
        
        # Calculate position cost
        position_cost = qty * entry_price
        
        # Check available capital
        if position_cost > self.available:
            raise Exception(f"Insufficient capital: {self.available:.2f} USDT")
        
        # Create position
        position = {
            'symbol': symbol,
            'side': side,
            'entry_price': entry_price,
            'qty': qty,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'opened_at': datetime.utcnow(),
            'cost': position_cost,
            'current_price': entry_price,
            'pnl': 0.0,
            'pnl_pct': 0.0
        }
        
        # Update available capital
        self.available -= position_cost
        
        # Store position
        self.positions[symbol] = position
        
        return position
    
    def update_positions(self, symbol: str, current_price: float) -> List[Dict]:
        """
        Update position with current price and check for SL/TP hits.
        
        Args:
            symbol: Trading pair
            current_price: Current market price
        
        Returns:
            List of closed positions (if any)
        """
        closed_positions = []
        
        if symbol not in self.positions:
            return closed_positions
        
        position = self.positions[symbol]
        position['current_price'] = current_price
        
        # Calculate P&L
        if position['side'] == 'long':
            pnl = (current_price - position['entry_price']) * position['qty']
            pnl_pct = ((current_price / position['entry_price']) - 1) * 100
            
            # Check SL/TP
            if current_price <= position['stop_loss']:
                closed_position = self.close_position(symbol, position['stop_loss'], 'stop_loss')
                closed_positions.append(closed_position)
            elif current_price >= position['take_profit']:
                closed_position = self.close_position(symbol, position['take_profit'], 'take_profit')
                closed_positions.append(closed_position)
        
        else:  # short
            pnl = (position['entry_price'] - current_price) * position['qty']
            pnl_pct = ((position['entry_price'] / current_price) - 1) * 100
            
            # Check SL/TP
            if current_price >= position['stop_loss']:
                closed_position = self.close_position(symbol, position['stop_loss'], 'stop_loss')
                closed_positions.append(closed_position)
            elif current_price <= position['take_profit']:
                closed_position = self.close_position(symbol, position['take_profit'], 'take_profit')
                closed_positions.append(closed_position)
        
        # Update position
        position['pnl'] = pnl
        position['pnl_pct'] = pnl_pct
        
        return closed_positions
    
    def close_position(
        self,
        symbol: str,
        exit_price: float,
        exit_reason: str
    ) -> Dict:
        """
        Close a position.
        
        Args:
            symbol: Trading pair
            exit_price: Exit price
            exit_reason: Reason for exit ('stop_loss', 'take_profit', 'manual')
        
        Returns:
            Closed position dict
        """
        if symbol not in self.positions:
            raise Exception(f"Position {symbol} not found")
        
        position = self.positions[symbol]
        
        # Calculate final P&L
        if position['side'] == 'long':
            pnl = (exit_price - position['entry_price']) * position['qty']
            pnl_pct = ((exit_price / position['entry_price']) - 1) * 100
        else:  # short
            pnl = (position['entry_price'] - exit_price) * position['qty']
            pnl_pct = ((position['entry_price'] / exit_price) - 1) * 100
        
        # Update equity and available capital
        position_value = exit_price * position['qty']
        self.available += position_value
        self.equity = self.available + sum(p['cost'] for p in self.positions.values() if p['symbol'] != symbol)
        
        # Update daily P&L
        self.daily_pnl += pnl
        
        # Create closed position record
        closed_position = {
            **position,
            'exit_price': exit_price,
            'exit_reason': exit_reason,
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'closed_at': datetime.utcnow()
        }
        
        # Remove from positions
        del self.positions[symbol]
        
        return closed_position
    
    def get_status(self) -> Dict:
        """
        Get current engine status.
        
        Returns:
            Dict with equity, available capital, and positions
        """
        return {
            'equity': self.equity,
            'available': self.available,
            'positions': list(self.positions.values()),
            'daily_pnl': self.daily_pnl,
            'daily_pnl_pct': (self.daily_pnl / self.initial_capital) * 100
        }
    
    def reset_daily_pnl(self):
        """Reset daily P&L counter (call at start of each day)."""
        self.daily_pnl = 0.0
