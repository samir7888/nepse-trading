"""
Beginner-Friendly NEPSE Trading System
Optimized for small capital (3000 NPR) with enhanced price validation
"""
import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
from typing import Dict, List
import logging
from tqdm import tqdm

from data_fetcher import NepseDataFetcher
from signal_generator import TradingSignalGenerator
from backtesting_engine import BacktestingEngine
from config import TRADING_RULES, BACKTEST_CONFIG, OUTPUT_DIR, INVESTMENT_CAPITAL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BeginnerTradingSystem:
    def __init__(self, capital: float = None):
        # Use capital from config.py if not provided
        self.capital = capital if capital is not None else INVESTMENT_CAPITAL['total_budget']
        self.max_per_stock = INVESTMENT_CAPITAL['max_per_stock']
        self.recommended_per_stock = INVESTMENT_CAPITAL['recommended_per_stock']
        self.cash_reserve = INVESTMENT_CAPITAL['cash_reserve']
        self.min_investment = INVESTMENT_CAPITAL['min_investment']
        self.max_positions = INVESTMENT_CAPITAL['max_positions']
        
        self.data_fetcher = NepseDataFetcher()
        self.signal_generator = TradingSignalGenerator()
        self.backtest_engine = BacktestingEngine(initial_capital=self.capital)
        
        # Create output directory
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        logger.info(f"Initialized system with NPR {self.capital:,} budget")
        logger.info(f"Max per stock: {self.max_per_stock*100:.0f}% (NPR {self.capital*self.max_per_stock:,.0f})")
        logger.info(f"Recommended per stock: {self.recommended_per_stock*100:.0f}% (NPR {self.capital*self.recommended_per_stock:,.0f})")
        logger.info(f"Cash reserve: {self.cash_reserve*100:.0f}% (NPR {self.capital*self.cash_reserve:,.0f})")
        
    def validate_price_data(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """Validate and clean price data to fix high/low issues"""
        if df.empty:
            return df
        
        df_clean = df.copy()
        
        # Fix obvious data errors
        for i in range(len(df_clean)):
            row = df_clean.iloc[i]
            
            # High should be >= Close and Open
            if 'high' in df_clean.columns and 'close' in df_clean.columns:
                if row['high'] < row['close']:
                    df_clean.iloc[i, df_clean.columns.get_loc('high')] = row['close']
                    logger.warning(f"{symbol}: Fixed high price on {df_clean.index[i]}")
            
            # Low should be <= Close and Open  
            if 'low' in df_clean.columns and 'close' in df_clean.columns:
                if row['low'] > row['close']:
                    df_clean.iloc[i, df_clean.columns.get_loc('low')] = row['close']
                    logger.warning(f"{symbol}: Fixed low price on {df_clean.index[i]}")
            
            # Volume should be positive
            if 'volume' in df_clean.columns and row['volume'] < 0:
                df_clean.iloc[i, df_clean.columns.get_loc('volume')] = 0
        
        return df_clean
    
    def get_beginner_friendly_stocks(self) -> List[Dict]:
        """Get stocks suitable for beginners with small capital"""
        logger.info("Fetching beginner-friendly stocks...")
        
        # Get companies list first
        companies = self.data_fetcher.get_companies_list()
        
        if not companies:
            logger.warning("No companies data available")
            return []
        
        # Get price volume data to find actively traded stocks
        logger.info("Fetching price and volume data...")
        try:
            price_volume_data = self.data_fetcher._get_price_volume_for_sorting()
            if not price_volume_data:
                logger.warning("No price volume data available")
                return []
        except Exception as e:
            logger.error(f"Failed to get price volume data: {e}")
            return []
        
        # Create symbol to company mapping
        symbol_to_company = {comp.get('symbol'): comp for comp in companies}
        
        # Filter for beginner-friendly stocks
        suitable_stocks = []
        
        for price_data in price_volume_data:
            symbol = price_data.get('symbol', '')
            
            # Get company info
            company_info = symbol_to_company.get(symbol, {})
            
            # Get price and volume
            try:
                price = float(price_data.get('lastTradedPrice', 0) or 0)
                volume = float(price_data.get('totalTradeQuantity', 0) or 0)
            except (ValueError, TypeError):
                continue
            
            # Skip if no valid price data
            if price <= 0:
                continue
            
            # Beginner-friendly criteria:
            # 1. Price between 50-2500 NPR (affordable for 3000 NPR budget)
            # 2. Some trading activity
            if 50 <= price <= 2500:
                # Combine company info with price data
                stock_data = {**company_info, **price_data}
                stock_data['lastTradedPrice'] = price
                suitable_stocks.append(stock_data)
        
        # Sort by trading activity (volume * price)
        suitable_stocks.sort(key=lambda x: float(x.get('totalTradeQuantity', 0)) * float(x.get('lastTradedPrice', 0)), reverse=True)
        
        logger.info(f"Found {len(suitable_stocks)} beginner-friendly stocks")
        return suitable_stocks[:25]  # Top 25 for analysis
    
    def calculate_position_size_for_beginner(self, price: float, available_capital: float) -> Dict:
        """Calculate appropriate position size based on config.py settings"""
        if price <= 0:
            return {'shares': 0, 'value': 0, 'reason': 'Invalid price'}
        
        # Use settings from config.py
        max_position_value = min(
            self.capital * self.max_per_stock,  # Max % from config
            available_capital * 0.8  # Don't use all available capital at once
        )
        recommended_position_value = self.capital * self.recommended_per_stock
        min_position_value = self.min_investment
        
        # Calculate shares for different scenarios
        max_shares = int(max_position_value / price)
        recommended_shares = int(recommended_position_value / price)
        min_shares = int(min_position_value / price)
        
        # Check if stock is affordable
        if max_shares < min_shares:
            return {
                'shares': 0, 
                'value': 0, 
                'reason': f'Stock too expensive - need NPR {min_position_value:,.0f} minimum but max allowed is NPR {max_position_value:,.0f}'
            }
        
        # Use recommended shares, but ensure it's within limits
        final_shares = max(min_shares, min(recommended_shares, max_shares))
        final_value = final_shares * price
        
        # Final validation
        if final_value > available_capital:
            # Adjust to available capital
            final_shares = int(available_capital * 0.8 / price)
            final_value = final_shares * price
            
            if final_shares < min_shares:
                return {
                    'shares': 0, 
                    'value': 0, 
                    'reason': f'Insufficient capital - need NPR {min_position_value:,.0f} but only NPR {available_capital:,.0f} available'
                }
        
        return {
            'shares': final_shares,
            'value': final_value,
            'percentage_of_capital': (final_value / self.capital) * 100,
            'percentage_of_available': (final_value / available_capital) * 100,
            'reason': 'Suitable for investment',
            'max_allowed': max_position_value,
            'recommended_amount': recommended_position_value
        }
    
    def run_beginner_analysis(self) -> Dict:
        """Run complete analysis optimized for beginners"""
        logger.info("Starting Beginner Trading System Analysis...")
        
        # Step 1: Get suitable stocks
        suitable_stocks = self.get_beginner_friendly_stocks()
        
        if not suitable_stocks:
            logger.error("No suitable stocks found for beginners")
            return {}
        
        # Step 2: Fetch and validate historical data
        symbols = [stock['symbol'] for stock in suitable_stocks]
        logger.info(f"Fetching historical data for {len(symbols)} stocks...")
        
        historical_data = {}
        for symbol in tqdm(symbols, desc="Fetching data"):
            try:
                df = self.data_fetcher.get_historical_data(symbol, days=500)
                if not df.empty:
                    # Validate and clean the data
                    df_clean = self.validate_price_data(df, symbol)
                    historical_data[symbol] = df_clean
            except Exception as e:
                logger.warning(f"Failed to fetch data for {symbol}: {e}")
                continue
        
        logger.info(f"Successfully fetched data for {len(historical_data)} stocks")
        
        # Step 3: Generate signals with validation
        current_signals = self.generate_beginner_signals(historical_data, suitable_stocks)
        
        # Step 4: Run backtesting
        backtest_results = self.run_beginner_backtest(historical_data)
        
        # Step 5: Create beginner-friendly output
        self.create_beginner_excel_output(
            current_signals, backtest_results, suitable_stocks, historical_data
        )
        
        return {
            'current_signals': current_signals,
            'backtest_results': backtest_results,
            'suitable_stocks': suitable_stocks,
            'capital': self.capital
        }
    
    def generate_beginner_signals(self, historical_data: Dict, stock_info: List[Dict]) -> pd.DataFrame:
        """Generate trading signals with beginner-friendly analysis using CURRENT market prices"""
        
        # Get current market prices first
        try:
            current_price_data = self.data_fetcher._get_price_volume_for_sorting()
            if not current_price_data:
                logger.warning("No current price data available")
                return pd.DataFrame()
        except Exception as e:
            logger.error(f"Failed to get current prices: {e}")
            return pd.DataFrame()
        
        # Create current price lookup
        current_prices = {}
        for stock in current_price_data:
            symbol = stock.get('symbol', '')
            price = float(stock.get('lastTradedPrice', 0))
            if price > 0:
                current_prices[symbol] = {
                    'price': price,
                    'volume': float(stock.get('totalTradeQuantity', 0))
                }
        
        logger.info(f"Got current prices for {len(current_prices)} stocks")
        
        # Generate signals based on CURRENT prices, not historical
        signals = []
        total_budget_used = 0
        max_budget_usage = self.capital * 0.7  # Use max 70% of budget
        
        # Create stock info lookup
        stock_lookup = {stock['symbol']: stock for stock in stock_info}
        
        # Sort stocks by trading activity (volume * price)
        sorted_stocks = []
        for symbol in current_prices:
            if symbol in historical_data and not historical_data[symbol].empty:
                price_info = current_prices[symbol]
                activity_score = price_info['price'] * price_info['volume']
                sorted_stocks.append((symbol, activity_score, price_info['price']))
        
        sorted_stocks.sort(key=lambda x: x[1], reverse=True)
        
        for symbol, activity_score, current_price in sorted_stocks:
            if total_budget_used >= max_budget_usage:
                break
                
            # Check if price is suitable for beginners
            if not (50 <= current_price <= 1500):  # Conservative price range
                continue
            
            df = historical_data[symbol]
            
            # Generate signals using historical data for momentum analysis
            symbol_signals = self.signal_generator.generate_buy_signals(df, symbol)
            
            if not symbol_signals.empty:
                # Use CURRENT market price, not historical entry price
                stock_data = stock_lookup.get(symbol, {})
                
                # Calculate position sizing based on CURRENT price
                position_info = self.calculate_position_size_for_beginner(current_price, self.capital - total_budget_used)
                
                if position_info['shares'] > 0 and position_info['value'] <= (self.capital - total_budget_used):
                    # Create signal with current market data
                    signal_data = {
                        'symbol': symbol,
                        'entry_price': current_price,  # Use CURRENT price as entry
                        'current_market_price': current_price,
                        'stop_loss': current_price * 0.7,  # 30% stop loss
                        'target_price': current_price * 1.6,  # 60% target
                        'recommended_shares': position_info['shares'],
                        'recommended_investment': position_info['value'],
                        'percentage_of_capital': position_info.get('percentage_of_capital', 0),
                        'suitability': position_info['reason'],
                        'company_name': stock_data.get('companyName', symbol),
                        'volume': current_prices[symbol]['volume']
                    }
                    
                    # Risk assessment based on current price
                    risk_amount = (current_price - signal_data['stop_loss']) * position_info['shares']
                    signal_data['risk_amount_npr'] = risk_amount
                    signal_data['risk_percentage'] = (risk_amount / self.capital) * 100
                    
                    # Potential profit based on current price
                    profit_amount = (signal_data['target_price'] - current_price) * position_info['shares']
                    signal_data['potential_profit_npr'] = profit_amount
                    
                    # Risk-reward ratio
                    signal_data['risk_reward_ratio'] = profit_amount / risk_amount if risk_amount > 0 else 0
                    
                    # Only add if risk-reward is acceptable (at least 1.5:1)
                    if signal_data['risk_reward_ratio'] >= 1.5:
                        signals.append(signal_data)
                        total_budget_used += position_info['value']
                        
                        if len(signals) >= 4:  # Limit to 4 recommendations max
                            break
        
        if signals:
            combined_signals = pd.DataFrame(signals)
            # Sort by risk-reward ratio (best first)
            combined_signals = combined_signals.sort_values('risk_reward_ratio', ascending=False)
            
            logger.info(f"Generated {len(combined_signals)} signals using current market prices")
            logger.info(f"Total budget allocation: NPR {total_budget_used:.2f} ({(total_budget_used/self.capital)*100:.1f}%)")
            
            return combined_signals
        
        return pd.DataFrame()
    
    def run_beginner_backtest(self, historical_data: Dict) -> Dict:
        """Run backtesting with beginner-friendly parameters"""
        logger.info("Running beginner-friendly backtesting...")
        
        # Use shorter backtest period for more relevant results
        start_date = datetime.now() - timedelta(days=365)  # 1 year
        end_date = datetime.now()
        
        all_signals = []
        
        for symbol, df in historical_data.items():
            if df.empty or len(df) < 50:
                continue
            
            # Filter for backtest period
            backtest_data = df[(df.index >= start_date) & (df.index <= end_date)]
            
            if len(backtest_data) < 30:
                continue
            
            signals = self.signal_generator.generate_buy_signals(backtest_data, symbol)
            if not signals.empty:
                all_signals.append(signals)
        
        if not all_signals:
            return {'performance_metrics': {}, 'closed_trades': pd.DataFrame()}
        
        combined_signals = pd.concat(all_signals, ignore_index=True)
        combined_signals = self.signal_generator.filter_signals_by_risk_reward(combined_signals)
        
        # Simulate with beginner constraints
        return self.simulate_beginner_trading(combined_signals, historical_data)
    
    def simulate_beginner_trading(self, signals: pd.DataFrame, historical_data: Dict) -> Dict:
        """Simulate trading with beginner-friendly constraints"""
        if signals.empty:
            return {'performance_metrics': {}, 'closed_trades': pd.DataFrame()}
        
        # Reset backtest engine for beginner simulation
        self.backtest_engine = BacktestingEngine(initial_capital=self.capital)
        
        # Sort signals by date
        signals = signals.sort_index()
        
        # Get simulation date range
        start_date = signals.index.min()
        end_date = datetime.now()
        
        simulation_dates = pd.date_range(start=start_date, end=end_date, freq='D')
        
        for current_date in tqdm(simulation_dates, desc="Simulating trades"):
            # Record portfolio snapshot
            self.backtest_engine.record_portfolio_snapshot(current_date)
            
            # Check for new signals (limit to 1 position for beginners)
            if len(self.backtest_engine.positions) < 2:  # Max 2 positions for beginners
                # Handle different index types for date filtering
                if hasattr(signals.index, 'date'):
                    daily_signals = signals[signals.index.date == current_date.date()]
                else:
                    signal_dates = pd.to_datetime(signals.index).date
                    daily_signals = signals[signal_dates == current_date.date()]
                
                for _, signal in daily_signals.iterrows():
                    symbol = signal['symbol']
                    entry_price = signal['entry_price']
                    
                    # Use beginner position sizing
                    position_info = self.calculate_position_size_for_beginner(entry_price, self.backtest_engine.current_capital)
                    
                    if position_info['shares'] > 0:
                        # Override the backtest engine's position sizing
                        success = self.open_beginner_position(
                            symbol, current_date, entry_price, 
                            signal['stop_loss'], signal['target_price'],
                            position_info['shares']
                        )
                        if success:
                            break  # Only one position per day for beginners
            
            # Update and check positions
            self.update_and_check_positions(current_date, historical_data)
        
        # Calculate performance
        performance_metrics = self.backtest_engine.calculate_performance_metrics()
        
        return {
            'performance_metrics': performance_metrics,
            'closed_trades': self.backtest_engine.closed_trades,
            'portfolio_history': pd.DataFrame(self.backtest_engine.portfolio_history)
        }
    
    def open_beginner_position(self, symbol: str, entry_date: datetime, entry_price: float,
                             stop_loss: float, target_price: float, shares: int) -> bool:
        """Open position with predetermined share count for beginners"""
        trade_value = shares * entry_price
        commission = trade_value * self.backtest_engine.commission_rate
        total_cost = trade_value + commission
        
        if total_cost > self.backtest_engine.current_capital:
            return False
        
        # Create position manually
        new_position = {
            'symbol': symbol,
            'entry_date': entry_date,
            'entry_price': entry_price,
            'quantity': shares,
            'stop_loss': stop_loss,
            'target_price': target_price,
            'current_price': entry_price,
            'highest_price': entry_price,
            'commission_paid': commission,
            'unrealized_pnl': 0.0
        }
        
        self.backtest_engine.positions = pd.concat([
            self.backtest_engine.positions,
            pd.DataFrame([new_position])
        ], ignore_index=True)
        
        self.backtest_engine.current_capital -= total_cost
        return True
    
    def update_and_check_positions(self, current_date: datetime, historical_data: Dict):
        """Update positions and check for exits"""
        if self.backtest_engine.positions.empty:
            return
        
        # Get current prices
        current_data = {}
        for symbol in self.backtest_engine.positions['symbol'].unique():
            if symbol in historical_data:
                symbol_data = historical_data[symbol]
                current_day_data = symbol_data[symbol_data.index.date == current_date.date()]
                
                if not current_day_data.empty:
                    current_data[symbol] = {
                        'close': current_day_data['close'].iloc[-1],
                        'high': current_day_data['high'].iloc[-1],
                        'low': current_day_data['low'].iloc[-1]
                    }
        
        # Update positions
        self.backtest_engine.update_positions(current_data)
        
        # Check for exits
        positions_to_close = []
        
        for _, position in self.backtest_engine.positions.iterrows():
            symbol = position['symbol']
            current_price = position['current_price']
            target_price = position['target_price']
            stop_loss = position['stop_loss']
            
            if current_price <= 0:
                continue
            
            # Simple exit rules for beginners
            if current_price >= target_price:
                positions_to_close.append((symbol, current_price, "Target Reached"))
            elif current_price <= stop_loss:
                positions_to_close.append((symbol, current_price, "Stop Loss"))
        
        # Close positions
        for symbol, exit_price, reason in positions_to_close:
            self.backtest_engine.close_position(symbol, current_date, exit_price, reason)
    
    def create_beginner_excel_output(self, signals: pd.DataFrame, backtest_results: Dict,
                                   stock_info: List[Dict], historical_data: Dict):
        """Create beginner-friendly Excel output"""
        excel_file = os.path.join(OUTPUT_DIR, "beginner_trading_strategy.xlsx")
        
        with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
            
            # Sheet 1: Investment Recommendations
            if not signals.empty:
                recommendations = signals.copy()
                recommendations = recommendations[[
                    'symbol', 'company_name', 'entry_price', 'current_market_price',
                    'recommended_shares', 'recommended_investment', 'percentage_of_capital',
                    'stop_loss', 'target_price', 'risk_amount_npr', 'potential_profit_npr',
                    'risk_reward_ratio', 'suitability'
                ]].round(2)
                
                recommendations.to_excel(writer, sheet_name='Investment_Recommendations', index=False)
            else:
                pd.DataFrame({'Message': ['No suitable investment opportunities found at this time']}).to_excel(
                    writer, sheet_name='Investment_Recommendations', index=False
                )
            
            # Sheet 2: Beginner Performance Summary
            if 'performance_metrics' in backtest_results:
                metrics = backtest_results['performance_metrics']
                performance_summary = pd.DataFrame([
                    ['Your Investment Capital', f"NPR {self.capital:,}"],
                    ['Expected Annual Return', f"{metrics.get('cagr_percent', 0):.1f}%"],
                    ['Expected Monthly Return', f"{metrics.get('cagr_percent', 0)/12:.1f}%"],
                    ['Win Rate (Success Rate)', f"{metrics.get('win_rate_percent', 0):.1f}%"],
                    ['Average Profit per Winning Trade', f"NPR {metrics.get('avg_win_percent', 0) * self.capital / 100:.0f}"],
                    ['Average Loss per Losing Trade', f"NPR {abs(metrics.get('avg_loss_percent', 0)) * self.capital / 100:.0f}"],
                    ['Maximum Drawdown (Worst Loss)', f"{metrics.get('max_drawdown_percent', 0):.1f}%"],
                    ['Total Trades in Backtest', metrics.get('total_trades', 0)],
                    ['Risk Level', 'Moderate (Suitable for Beginners)'],
                    ['Recommended Position Size', '30-40% of capital per trade']
                ], columns=['Metric', 'Value'])
                
                performance_summary.to_excel(writer, sheet_name='Performance_Summary', index=False)
            
            # Sheet 3: Sample Trade History
            if 'closed_trades' in backtest_results and not backtest_results['closed_trades'].empty:
                trades = backtest_results['closed_trades'].copy()
                trades['entry_date'] = trades['entry_date'].dt.strftime('%Y-%m-%d')
                trades['exit_date'] = trades['exit_date'].dt.strftime('%Y-%m-%d')
                trades = trades.round(2)
                
                trades.to_excel(writer, sheet_name='Sample_Trades', index=False)
            
            # Sheet 4: Beginner Guidelines
            guidelines = pd.DataFrame([
                ['Rule', 'Description', 'Why Important'],
                ['Start Small', 'Begin with 500-1000 NPR per trade', 'Learn without big losses'],
                ['Use Stop Loss', 'Always set 30% stop loss', 'Protect your capital'],
                ['Take Profits', 'Sell at 60% profit target', 'Lock in gains'],
                ['Limit Positions', 'Maximum 2 stocks at once', 'Reduce risk'],
                ['Keep Cash', 'Always keep 50% in cash', 'Ready for opportunities'],
                ['Follow System', 'Stick to the signals', 'Remove emotions'],
                ['Track Everything', 'Record all trades', 'Learn from experience'],
                ['Review Monthly', 'Check performance monthly', 'Continuous improvement'],
                ['Stay Disciplined', 'Follow rules strictly', 'Long-term success']
            ])
            
            guidelines.to_excel(writer, sheet_name='Beginner_Guidelines', index=False, header=False)
            
            # Sheet 5: Stock Information
            if stock_info:
                stock_df = pd.DataFrame(stock_info)
                # Select relevant columns for beginners
                if not stock_df.empty:
                    beginner_cols = ['symbol', 'companyName', 'lastTradedPrice', 'totalTradeQuantity', 'marketCapitalization']
                    available_cols = [col for col in beginner_cols if col in stock_df.columns]
                    stock_df = stock_df[available_cols]
                
                stock_df.to_excel(writer, sheet_name='Stock_Information', index=False)
        
        logger.info(f"Beginner-friendly Excel report created: {excel_file}")
        return excel_file

if __name__ == "__main__":
    # Run the beginner trading system using config.py settings
    system = BeginnerTradingSystem()  # Will use INVESTMENT_CAPITAL from config.py
    results = system.run_beginner_analysis()
    
    if results:
        print(f"\n{'='*60}")
        print("🎯 NEPSE BEGINNER TRADING STRATEGY - YOUR PERSONALIZED REPORT")
        print(f"{'='*60}")
        print(f"💰 Your Investment Budget: NPR {results['capital']:,}")
        
        if 'current_signals' in results and not results['current_signals'].empty:
            signals = results['current_signals']
            print(f"\n📈 CURRENT INVESTMENT OPPORTUNITIES: {len(signals)}")
            print("-" * 50)
            
            for i, (_, signal) in enumerate(signals.head(3).iterrows(), 1):
                print(f"{i}. {signal['symbol']} ({signal.get('company_name', 'N/A')})")
                print(f"   💵 Buy Price: NPR {signal['entry_price']:.2f}")
                print(f"   📊 Recommended Investment: NPR {signal.get('recommended_investment', 0):.0f}")
                print(f"   🎯 Target Price: NPR {signal['target_price']:.2f}")
                print(f"   🛡️  Stop Loss: NPR {signal['stop_loss']:.2f}")
                print(f"   💡 Potential Profit: NPR {signal.get('potential_profit_npr', 0):.0f}")
                print()
        else:
            print("\n📈 CURRENT INVESTMENT OPPORTUNITIES: None at this time")
            print("💡 Keep monitoring - new opportunities appear regularly!")
        
        if 'backtest_results' in results and 'performance_metrics' in results['backtest_results']:
            metrics = results['backtest_results']['performance_metrics']
            print(f"\n📊 STRATEGY PERFORMANCE (Based on Historical Data):")
            print("-" * 50)
            print(f"📈 Expected Annual Return: {metrics.get('cagr_percent', 0):.1f}%")
            print(f"💰 Expected Monthly Profit: NPR {metrics.get('cagr_percent', 0) * 3000 / 100 / 12:.0f}")
            print(f"🎯 Success Rate: {metrics.get('win_rate_percent', 0):.1f}%")
            print(f"📉 Maximum Loss Period: {metrics.get('max_drawdown_percent', 0):.1f}%")
            print(f"🔄 Total Trades Analyzed: {metrics.get('total_trades', 0)}")
        
        print(f"\n📋 NEXT STEPS FOR YOU:")
        print("-" * 30)
        print("1. 📖 Read the detailed Excel report")
        print("2. 🎓 Study the beginner guidelines")
        print("3. 📝 Start with paper trading (practice)")
        print("4. 💰 Begin with small amounts (500-1000 NPR)")
        print("5. 📊 Track your progress weekly")
        
        print(f"\n📄 Detailed report saved to: output/beginner_trading_strategy.xlsx")
        print(f"{'='*60}")
    else:
        print("❌ System analysis failed. Please check your internet connection and try again.")