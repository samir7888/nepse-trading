"""
Backtesting Engine Module
Handles portfolio management, position sizing, and performance tracking
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging
from config import BACKTEST_CONFIG, TRADING_RULES

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BacktestingEngine:
    def __init__(self, initial_capital: float = None):
        self.initial_capital = initial_capital or BACKTEST_CONFIG['initial_capital']
        self.current_capital = self.initial_capital
        self.commission_rate = BACKTEST_CONFIG['commission_rate']
        self.min_trade_amount = BACKTEST_CONFIG['min_trade_amount']
        self.max_exposure = TRADING_RULES['max_capital_exposure'] / 100
        
        # Portfolio tracking
        self.positions = pd.DataFrame()
        self.closed_trades = pd.DataFrame()
        self.portfolio_history = []
        self.cash_history = []
        
    def calculate_position_size(self, entry_price: float, stop_loss: float) -> int:
        """Calculate position size based on risk management rules"""
        if entry_price <= 0 or stop_loss <= 0:
            return 0
        
        # Calculate risk per share
        risk_per_share = entry_price - stop_loss
        
        # Maximum risk per trade (2% of capital)
        max_risk_per_trade = self.current_capital * 0.02
        
        # Calculate maximum shares based on risk
        max_shares_by_risk = int(max_risk_per_trade / risk_per_share)
        
        # Calculate maximum shares based on capital exposure
        available_capital = self.current_capital * self.max_exposure
        current_exposure = self.get_current_exposure()
        remaining_capital = available_capital - current_exposure
        
        max_shares_by_capital = int(remaining_capital / entry_price)
        
        # Take the minimum of both constraints
        position_size = min(max_shares_by_risk, max_shares_by_capital)
        
        # Ensure minimum trade amount
        if position_size * entry_price < self.min_trade_amount:
            return 0
        
        return max(0, position_size)
    
    def get_current_exposure(self) -> float:
        """Calculate current capital exposure from open positions"""
        if self.positions.empty:
            return 0.0
        
        return (self.positions['quantity'] * self.positions['current_price']).sum()
    
    def open_position(self, symbol: str, entry_date: datetime, entry_price: float, 
                     stop_loss: float, target_price: float) -> bool:
        """Open a new position"""
        position_size = self.calculate_position_size(entry_price, stop_loss)
        
        if position_size <= 0:
            logger.warning(f"Cannot open position for {symbol}: insufficient capital or risk too high")
            return False
        
        trade_value = position_size * entry_price
        commission = trade_value * self.commission_rate
        total_cost = trade_value + commission
        
        if total_cost > self.current_capital:
            logger.warning(f"Cannot open position for {symbol}: insufficient cash")
            return False
        
        # Create new position
        new_position = {
            'symbol': symbol,
            'entry_date': entry_date,
            'entry_price': entry_price,
            'quantity': position_size,
            'stop_loss': stop_loss,
            'target_price': target_price,
            'current_price': entry_price,
            'highest_price': entry_price,
            'commission_paid': commission,
            'unrealized_pnl': 0.0
        }
        
        # Add to positions
        self.positions = pd.concat([
            self.positions, 
            pd.DataFrame([new_position])
        ], ignore_index=True)
        
        # Update cash
        self.current_capital -= total_cost
        
        logger.info(f"Opened position: {symbol} - {position_size} shares at NPR {entry_price:.2f}")
        return True
    
    def close_position(self, symbol: str, exit_date: datetime, exit_price: float, reason: str) -> bool:
        """Close an existing position"""
        if self.positions.empty:
            return False
        
        position_idx = self.positions[self.positions['symbol'] == symbol].index
        if len(position_idx) == 0:
            return False
        
        position = self.positions.loc[position_idx[0]]
        
        trade_value = position['quantity'] * exit_price
        commission = trade_value * self.commission_rate
        net_proceeds = trade_value - commission
        
        # Calculate P&L
        total_cost = position['quantity'] * position['entry_price'] + position['commission_paid']
        total_commission = position['commission_paid'] + commission
        profit_loss = net_proceeds - (total_cost - position['commission_paid'])
        profit_loss_percent = (profit_loss / (total_cost - position['commission_paid'])) * 100
        
        # Record closed trade
        closed_trade = {
            'symbol': symbol,
            'entry_date': position['entry_date'],
            'exit_date': exit_date,
            'entry_price': position['entry_price'],
            'exit_price': exit_price,
            'quantity': position['quantity'],
            'profit_loss': profit_loss,
            'profit_loss_percent': profit_loss_percent,
            'total_commission': total_commission,
            'days_held': (exit_date - position['entry_date']).days,
            'reason': reason
        }
        
        self.closed_trades = pd.concat([
            self.closed_trades,
            pd.DataFrame([closed_trade])
        ], ignore_index=True)
        
        # Update cash
        self.current_capital += net_proceeds
        
        # Remove from positions
        self.positions = self.positions.drop(position_idx[0]).reset_index(drop=True)
        
        logger.info(f"Closed position: {symbol} - P&L: NPR {profit_loss:.2f} ({profit_loss_percent:.2f}%)")
        return True
    
    def update_positions(self, current_data: Dict[str, Dict]) -> None:
        """Update current prices and unrealized P&L for open positions"""
        if self.positions.empty:
            return
        
        for idx, position in self.positions.iterrows():
            symbol = position['symbol']
            if symbol in current_data and 'close' in current_data[symbol]:
                current_price = current_data[symbol]['close']
                
                # Update current price and highest price
                self.positions.loc[idx, 'current_price'] = current_price
                self.positions.loc[idx, 'highest_price'] = max(
                    position['highest_price'], current_price
                )
                
                # Calculate unrealized P&L
                unrealized_pnl = (current_price - position['entry_price']) * position['quantity']
                self.positions.loc[idx, 'unrealized_pnl'] = unrealized_pnl
    
    def get_portfolio_value(self) -> float:
        """Calculate total portfolio value"""
        cash = self.current_capital
        positions_value = 0.0
        
        if not self.positions.empty:
            positions_value = (self.positions['quantity'] * self.positions['current_price']).sum()
        
        return cash + positions_value
    
    def record_portfolio_snapshot(self, date: datetime) -> None:
        """Record portfolio snapshot for performance tracking"""
        portfolio_value = self.get_portfolio_value()
        
        snapshot = {
            'date': date,
            'portfolio_value': portfolio_value,
            'cash': self.current_capital,
            'positions_value': portfolio_value - self.current_capital,
            'num_positions': len(self.positions),
            'unrealized_pnl': self.positions['unrealized_pnl'].sum() if not self.positions.empty else 0
        }
        
        self.portfolio_history.append(snapshot)
    
    def calculate_performance_metrics(self) -> Dict:
        """Calculate comprehensive performance metrics"""
        if not self.portfolio_history:
            return {}
        
        portfolio_df = pd.DataFrame(self.portfolio_history)
        portfolio_df['date'] = pd.to_datetime(portfolio_df['date'])
        portfolio_df.set_index('date', inplace=True)
        
        # Calculate returns
        portfolio_df['returns'] = portfolio_df['portfolio_value'].pct_change()
        portfolio_df['cumulative_returns'] = (1 + portfolio_df['returns']).cumprod() - 1
        
        # Basic metrics
        total_return = (portfolio_df['portfolio_value'].iloc[-1] / self.initial_capital - 1) * 100
        
        # CAGR calculation
        years = (portfolio_df.index[-1] - portfolio_df.index[0]).days / 365.25
        cagr = ((portfolio_df['portfolio_value'].iloc[-1] / self.initial_capital) ** (1/years) - 1) * 100 if years > 0 else 0
        
        # Volatility (annualized)
        volatility = portfolio_df['returns'].std() * np.sqrt(252) * 100
        
        # Sharpe ratio (assuming 5% risk-free rate)
        risk_free_rate = 0.05
        excess_returns = portfolio_df['returns'].mean() * 252 - risk_free_rate
        sharpe_ratio = excess_returns / (volatility / 100) if volatility > 0 else 0
        
        # Maximum drawdown
        rolling_max = portfolio_df['portfolio_value'].expanding().max()
        drawdown = (portfolio_df['portfolio_value'] - rolling_max) / rolling_max * 100
        max_drawdown = drawdown.min()
        
        # Trade statistics
        if not self.closed_trades.empty:
            win_rate = (self.closed_trades['profit_loss'] > 0).mean() * 100
            avg_win = self.closed_trades[self.closed_trades['profit_loss'] > 0]['profit_loss_percent'].mean()
            avg_loss = self.closed_trades[self.closed_trades['profit_loss'] < 0]['profit_loss_percent'].mean()
            profit_factor = abs(self.closed_trades[self.closed_trades['profit_loss'] > 0]['profit_loss'].sum() / 
                               self.closed_trades[self.closed_trades['profit_loss'] < 0]['profit_loss'].sum()) if len(self.closed_trades[self.closed_trades['profit_loss'] < 0]) > 0 else float('inf')
        else:
            win_rate = avg_win = avg_loss = profit_factor = 0
        
        return {
            'total_return_percent': total_return,
            'cagr_percent': cagr,
            'volatility_percent': volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown_percent': max_drawdown,
            'win_rate_percent': win_rate,
            'avg_win_percent': avg_win,
            'avg_loss_percent': avg_loss,
            'profit_factor': profit_factor,
            'total_trades': len(self.closed_trades),
            'final_portfolio_value': portfolio_df['portfolio_value'].iloc[-1],
            'max_positions': portfolio_df['num_positions'].max()
        }