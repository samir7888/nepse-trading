"""
Trading Signal Generator Module
Implements the trading rules and generates buy/sell signals
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging
from config import TRADING_RULES

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TradingSignalGenerator:
    def __init__(self):
        self.ath_window_months = TRADING_RULES['ath_window_months']
        self.stop_loss_percent = TRADING_RULES['stop_loss_percent']
        self.target_percent = TRADING_RULES['target_percent']
        self.trailing_stop_weeks = TRADING_RULES['trailing_stop_weeks']
    
    def calculate_all_time_high(self, df: pd.DataFrame) -> pd.Series:
        """Calculate rolling all-time high for the stock"""
        if df.empty or 'high' not in df.columns:
            return pd.Series(dtype=float)
        
        return df['high'].expanding().max()
    
    def detect_new_ath(self, df: pd.DataFrame, window_months: Tuple[int, int] = (4, 6)) -> pd.Series:
        """Detect when stock makes new all-time high within specified window"""
        if df.empty:
            return pd.Series(dtype=bool)
        
        ath = self.calculate_all_time_high(df)
        new_ath = pd.Series(False, index=df.index)
        
        # Check for new ATH in rolling windows
        for months in range(window_months[0], window_months[1] + 1):
            window_days = months * 30  # Approximate days in months
            rolling_max = df['high'].rolling(window=window_days, min_periods=1).max()
            is_new_ath = (df['high'] == rolling_max) & (df['high'] == ath)
            new_ath = new_ath | is_new_ath
        
        return new_ath
    
    def check_consistent_momentum(self, df: pd.DataFrame, lookback_months: int = 6) -> bool:
        """Check if stock shows consistent upward momentum"""
        if df.empty or len(df) < 30:
            return False
        
        lookback_days = lookback_months * 30
        recent_data = df.tail(min(lookback_days, len(df)))
        
        if len(recent_data) < 30:
            return False
        
        # Calculate momentum indicators
        price_change = (recent_data['close'].iloc[-1] - recent_data['close'].iloc[0]) / recent_data['close'].iloc[0]
        
        # Check for positive momentum (at least 10% growth in lookback period)
        momentum_threshold = 0.10
        
        # Check for consistent highs (at least 2 new highs in the period)
        new_aths = self.detect_new_ath(recent_data)
        ath_count = new_aths.sum()
        
        return price_change > momentum_threshold and ath_count >= 2
    
    def generate_buy_signals(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """Generate buy signals based on trading rules"""
        if df.empty:
            return pd.DataFrame()
        
        signals = pd.DataFrame(index=df.index)
        signals['symbol'] = symbol
        signals['close'] = df['close']
        signals['high'] = df['high']
        signals['volume'] = df.get('volume', 0)
        
        # Calculate ATH and new ATH signals
        signals['ath'] = self.calculate_all_time_high(df)
        signals['new_ath'] = self.detect_new_ath(df, self.ath_window_months)
        
        # Generate buy signals
        signals['buy_signal'] = False
        
        for i in range(len(signals)):
            if signals['new_ath'].iloc[i]:
                # Check if this represents consistent momentum
                current_date = signals.index[i]
                historical_data = df.loc[:current_date]
                
                if self.check_consistent_momentum(historical_data):
                    signals.loc[signals.index[i], 'buy_signal'] = True
        
        # Calculate entry prices and targets
        signals['entry_price'] = np.where(signals['buy_signal'], signals['close'], np.nan)
        signals['stop_loss'] = np.where(
            signals['buy_signal'], 
            signals['close'] * (1 - self.stop_loss_percent / 100), 
            np.nan
        )
        signals['target_price'] = np.where(
            signals['buy_signal'], 
            signals['close'] * (1 + self.target_percent / 100), 
            np.nan
        )
        
        return signals[signals['buy_signal']].copy()
    
    def calculate_trailing_stop(self, entry_price: float, current_price: float, 
                              highest_price: float, weeks_held: int) -> float:
        """Calculate trailing stop loss"""
        if weeks_held < self.trailing_stop_weeks:
            # Use initial stop loss
            return entry_price * (1 - self.stop_loss_percent / 100)
        
        # Update trailing stop every 5 weeks
        trailing_stop_percent = min(
            self.stop_loss_percent,
            (highest_price - entry_price) / entry_price * 100 * 0.5  # Trail at 50% of gains
        )
        
        return highest_price * (1 - trailing_stop_percent / 100)
    
    def generate_sell_signals(self, positions: pd.DataFrame, current_data: Dict) -> pd.DataFrame:
        """Generate sell signals for open positions"""
        if positions.empty:
            return pd.DataFrame()
        
        sell_signals = []
        current_date = datetime.now()
        
        for _, position in positions.iterrows():
            symbol = position['symbol']
            entry_price = position['entry_price']
            entry_date = position['entry_date']
            highest_price = position.get('highest_price', entry_price)
            
            if symbol not in current_data:
                continue
            
            current_price = current_data[symbol].get('close', 0)
            if current_price <= 0:
                continue
            
            # Calculate weeks held
            weeks_held = (current_date - entry_date).days / 7
            
            # Update highest price
            highest_price = max(highest_price, current_price)
            
            # Calculate trailing stop
            trailing_stop = self.calculate_trailing_stop(
                entry_price, current_price, highest_price, weeks_held
            )
            
            # Check sell conditions
            sell_reason = None
            
            # Target reached
            target_price = entry_price * (1 + self.target_percent / 100)
            if current_price >= target_price:
                sell_reason = "Target Reached"
            
            # Stop loss hit
            elif current_price <= trailing_stop:
                sell_reason = "Stop Loss"
            
            if sell_reason:
                profit_loss = (current_price - entry_price) / entry_price * 100
                
                sell_signals.append({
                    'symbol': symbol,
                    'entry_date': entry_date,
                    'exit_date': current_date,
                    'entry_price': entry_price,
                    'exit_price': current_price,
                    'profit_loss_percent': profit_loss,
                    'reason': sell_reason,
                    'days_held': (current_date - entry_date).days
                })
        
        return pd.DataFrame(sell_signals)
    
    def filter_signals_by_risk_reward(self, signals: pd.DataFrame) -> pd.DataFrame:
        """Filter signals based on risk-reward ratio"""
        if signals.empty:
            return signals
        
        # Calculate risk-reward ratio
        signals['risk'] = (signals['entry_price'] - signals['stop_loss']) / signals['entry_price'] * 100
        signals['reward'] = (signals['target_price'] - signals['entry_price']) / signals['entry_price'] * 100
        signals['risk_reward_ratio'] = signals['reward'] / signals['risk']
        
        # Filter based on risk-reward criteria
        min_rr = TRADING_RULES['min_risk_reward']
        max_rr = TRADING_RULES['max_risk_reward']
        
        filtered_signals = signals[
            (signals['risk_reward_ratio'] >= min_rr) & 
            (signals['risk_reward_ratio'] <= max_rr)
        ].copy()
        
        logger.info(f"Filtered {len(signals)} signals to {len(filtered_signals)} based on risk-reward ratio")
        
        return filtered_signals