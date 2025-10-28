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

# 💰 INVESTMENT CAPITAL CONFIGURATION - CHANGE THIS AS PER YOUR BUDGET
# =======================================================================

INVESTMENT_CAPITAL = {
    # 🎯 MAIN SETTING: Change this to your total investment budget
    'total_budget': 500000,        # Your total investment budget in NPR
    
    # 📊 POSITION SIZING RULES (as percentage of total budget)
    'max_per_stock': 0.30,       # Maximum 30% of budget per stock (NPR 900 for 3000 budget)
    'recommended_per_stock': 0.25, # Recommended 25% of budget per stock (NPR 750 for 3000 budget)
    'cash_reserve': 0.30,        # Keep 30% as cash reserve (NPR 900 for 3000 budget)
    
    # 💵 MINIMUM INVESTMENT RULES
    'min_investment': 500,       # Minimum investment per stock in NPR
    'max_positions': 4           # Maximum number of stocks to hold at once
}

# 📋 EXAMPLES FOR DIFFERENT BUDGETS:
# 
# For NPR 5,000 budget:
# 'total_budget': 5000
# Max per stock: NPR 1,500 (30%)
# Recommended per stock: NPR 1,250 (25%)
# Cash reserve: NPR 1,500 (30%)
#
# For NPR 10,000 budget:
# 'total_budget': 10000
# Max per stock: NPR 3,000 (30%)
# Recommended per stock: NPR 2,500 (25%)
# Cash reserve: NPR 3,000 (30%)
#
# For NPR 50,000 budget:
# 'total_budget': 50000
# Max per stock: NPR 15,000 (30%)
# Recommended per stock: NPR 12,500 (25%)
# Cash reserve: NPR 15,000 (30%)

# Backtesting Configuration
BACKTEST_CONFIG = {
    'start_date': datetime.now() - timedelta(days=3*365),  # 3 years back
    'end_date': datetime.now(),
    'initial_capital': INVESTMENT_CAPITAL['total_budget'],  # Uses your budget setting
    'commission_rate': 0.004,    # 0.4% commission (typical for Nepal)
    'min_trade_amount': INVESTMENT_CAPITAL['min_investment']  # Uses your minimum setting
}

# File paths
OUTPUT_DIR = "output"
EXCEL_OUTPUT = os.path.join(OUTPUT_DIR, "nepse_trading_signals.xlsx")
DATA_DIR = "data"