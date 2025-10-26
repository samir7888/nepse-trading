# NEPSE Stock Trading & Backtesting System

A comprehensive Python-based trading system for Nepal Stock Exchange (NEPSE) that implements momentum-based trading strategies with robust risk management and backtesting capabilities.

**✅ UPDATED**: Now uses the correct NEPSE API endpoints from the backend folder in this repository.

## 🎯 System Overview

This system focuses on the top 50 NEPSE companies and implements a momentum trading strategy based on all-time highs with strict risk management rules.

### Trading Strategy

- **Buy Signal**: Companies making new all-time highs every 4-6 months with consistent upward momentum
- **Stop Loss**: 30% below entry price with trailing stop mechanism
- **Target**: 60% profit from entry price
- **Risk Management**: Maximum 50% capital exposure, 1:2 to 1:3 risk-reward ratio

## 📊 Features

- **Real-time Data**: Fetches data from NEPSE API (https://nepseapi.surajrimal.dev)
- **Backtesting**: Tests strategy performance over 2-3 years of historical data
- **Risk Management**: Position sizing based on capital and risk constraints
- **Excel Output**: Comprehensive trading signals and analysis in Excel format
- **Performance Metrics**: CAGR, Sharpe ratio, win rate, maximum drawdown, etc.

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Internet connection for API access

### Installation

#### **Option 1: Local Backend Setup (Recommended)**

1. **Install main dependencies**:

```bash
pip install -r requirements.txt
```

2. **Setup local backend server**:

```bash
# Install backend
cd backend && pip install .

# Start server (keep this running)
cd example && python NepseServer.py
```

3. **Run trading system** (in new terminal):

```bash
python run_system.py
```

#### **Option 2: Remote API Setup**

1. **Install dependencies**:

```bash
pip install -r requirements.txt
```

2. **Update config for remote API**:
   Edit `config.py`: `BASE_URL = "https://nepseapi.surajrimal.dev"`

3. **Test and run**:

```bash
python api_test.py
python run_system.py
```

### Alternative Setup (Windows)

```bash
# Double-click or run:
setup_and_run.bat
```

### 🔧 Troubleshooting API Timeouts

If you see timeout errors, the system has multiple solutions:

1. **Automatic handling**: System now uses 30-90 second timeouts with retries
2. **Demo mode**: Works with sample data when API is slow/unavailable
3. **Local server**: Use the backend folder to run your own API server
4. **Detailed guide**: See [TIMEOUT_FIX_GUIDE.md](TIMEOUT_FIX_GUIDE.md) for complete solutions

```bash
# Quick timeout test
python api_test.py

# Run system (works even with API timeouts)
python run_system.py
```

## 📁 System Architecture

```
nepse_trading_system/
├── config.py              # Configuration and trading rules
├── data_fetcher.py         # NEPSE API data fetching
├── signal_generator.py     # Trading signal generation
├── backtesting_engine.py   # Portfolio management and backtesting
├── nepse_trading_system.py # Main system orchestrator
├── run_system.py          # Simple execution script
├── requirements.txt       # Python dependencies
└── output/                # Generated Excel files
    └── nepse_trading_signals.xlsx
```

## 📈 Trading Rules

### Entry Criteria

- Stock makes new all-time high within 4-6 month window
- Shows consistent upward momentum (>10% growth in lookback period)
- At least 2 new highs in the momentum period
- Risk-reward ratio between 1:2 and 1:3

### Exit Criteria

- **Target Hit**: 60% profit from entry
- **Stop Loss**: 30% loss from entry (with trailing mechanism)
- **Trailing Stop**: Updates every 5 weeks to lock in gains

### Risk Management

- Maximum 2% risk per trade
- Maximum 50% total capital exposure
- Minimum trade size: NPR 10,000
- Commission: 0.4% per trade

## 📊 Excel Output

The system generates a comprehensive Excel file with multiple sheets:

1. **Current_Signals**: Latest buy recommendations
2. **Performance_Summary**: Backtest metrics (CAGR, Sharpe ratio, etc.)
3. **All_Trades**: Complete trade history with P&L
4. **Portfolio_History**: Daily portfolio value tracking
5. **Companies_Info**: Top 50 company details
6. **Trading_Rules**: System configuration parameters

## 🔧 Configuration

Edit `config.py` to customize:

```python
TRADING_RULES = {
    'ath_window_months': (4, 6),    # ATH detection window
    'stop_loss_percent': 30,        # Stop loss percentage
    'target_percent': 60,           # Profit target
    'max_capital_exposure': 50,     # Maximum capital exposure
    'top_companies_count': 50       # Number of companies to analyze
}

BACKTEST_CONFIG = {
    'initial_capital': 1000000,     # Starting capital (NPR)
    'commission_rate': 0.004,       # 0.4% commission
    'min_trade_amount': 10000       # Minimum trade size
}
```

## 📋 Usage Examples

### Basic Usage

```bash
python run_system.py
```

### Programmatic Usage

```python
from nepse_trading_system import NepseTradingSystem

system = NepseTradingSystem()
results = system.run_full_system()

# Access results
current_signals = results['current_signals']
backtest_results = results['backtest_results']
excel_file = results['excel_file']
```

## 📊 Performance Metrics

The system calculates comprehensive performance metrics:

- **Total Return**: Overall portfolio return percentage
- **CAGR**: Compound Annual Growth Rate
- **Volatility**: Annualized portfolio volatility
- **Sharpe Ratio**: Risk-adjusted return measure
- **Maximum Drawdown**: Largest peak-to-trough decline
- **Win Rate**: Percentage of profitable trades
- **Profit Factor**: Ratio of gross profit to gross loss

## ⚠️ Important Notes

### Risk Disclaimer

- This system is for educational and research purposes
- Past performance does not guarantee future results
- Always conduct your own research before trading
- Consider consulting with financial advisors

### API Limitations

- Respects API rate limits with built-in delays
- Handles API errors gracefully
- May require internet connectivity throughout execution

### Data Quality

- System validates data quality before processing
- Filters out stocks with insufficient historical data
- Handles missing data points appropriately

## 🛠️ Troubleshooting

### Common Issues

1. **API Connection Errors**

   - Check internet connection
   - Verify API endpoint availability
   - Try running again after a few minutes

2. **No Signals Generated**

   - Market conditions may not meet criteria
   - Try adjusting parameters in config.py
   - Check if sufficient historical data is available

3. **Excel File Errors**
   - Ensure output directory has write permissions
   - Close any open Excel files with the same name
   - Check available disk space

### Debug Mode

Enable detailed logging by modifying the logging level:

```python
logging.basicConfig(level=logging.DEBUG)
```

## 🔄 System Workflow

1. **Data Collection**: Fetches top 50 NEPSE companies
2. **Historical Analysis**: Downloads 3 years of price data
3. **Signal Generation**: Identifies momentum-based buy opportunities
4. **Backtesting**: Simulates trading over historical period
5. **Current Analysis**: Generates current trading recommendations
6. **Excel Export**: Creates comprehensive trading report

## 📞 Support

For issues or questions:

- Check the troubleshooting section
- Review log messages for specific errors
- Ensure all dependencies are properly installed

## 📄 License

This project is provided as-is for educational purposes. Use at your own risk.

---

**Happy Trading! 📈**

_Remember: Always trade responsibly and never risk more than you can afford to lose._
