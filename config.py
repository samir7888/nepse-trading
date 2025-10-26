# Configuration file for NEPSE Trading System
import os
from datetime import datetime, timedelta

# API Configuration - Updated to use local backend server
BASE_URL = "http://localhost:8000"  # Local backend server from backend folder

# Timeout Configuration (adjust these if you're experiencing timeout issues)
API_TIMEOUTS = {
    'short': [15, 30, 45],      # For quick endpoints like market status
    'medium': [30, 60, 90],     # For medium endpoints like companies list
    'long': [60, 120, 180]      # For heavy endpoints like historical data
}

API_ENDPOINTS = {
    'companies': '/CompanyList',
    'price_volume': '/PriceVolume',
    'historical': '/DailyScripPriceGraph',  # Use daily price graph for historical data
    'market_status': '/IsNepseOpen',
    'summary': '/Summary',
    'live_market': '/LiveMarket',
    'top_gainers': '/TopGainers',
    'top_losers': '/TopLosers',
    'company_details': '/CompanyDetails',  # Note: Not available in local backend
    'nepse_index': '/NepseIndex',
    'sub_indices': '/NepseSubIndices',
    'floorsheet': '/Floorsheet',  # Note: Not available in local backend
    'daily_scrip_price': '/DailyScripPriceGraph',
    'market_depth': '/MarketDepth',
    'security_list': '/SecurityList',
    'trade_turnover': '/TradeTurnoverTransactionSubindices'
}

# Alternative API URLs (in case main URL is slow)
ALTERNATIVE_URLS = [
    "https://nepseapi.surajrimal.dev",
    # Add backup URLs here if available
]

# Trading Rules Configuration
TRADING_RULES = {
    'ath_window_months': (4, 6),  # 4-6 months window for ATH detection
    'stop_loss_percent': 30,      # 30% stop loss
    'target_percent': 60,         # 60% profit target
    'trailing_stop_weeks': 5,     # Update trailing stop every 5 weeks
    'max_capital_exposure': 50,   # Maximum 50% capital exposure
    'min_risk_reward': 2,         # Minimum 1:2 risk-reward ratio
    'max_risk_reward': 3,         # Maximum 1:3 risk-reward ratio
    'top_companies_count': 20     # Focus on top 50 companies
}

# Backtesting Configuration
BACKTEST_CONFIG = {
    'start_date': datetime.now() - timedelta(days=3*365),  # 3 years back
    'end_date': datetime.now(),
    'initial_capital': 3000,  # 3000 NPR - Your investment budget
    'commission_rate': 0.004,    # 0.4% commission (typical for Nepal)
    'min_trade_amount': 500    # Minimum 500 NPR per trade for small budget
}

# File paths
OUTPUT_DIR = "output"
EXCEL_OUTPUT = os.path.join(OUTPUT_DIR, "nepse_trading_signals.xlsx")
DATA_DIR = "data"