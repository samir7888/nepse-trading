#!/usr/bin/env python3
"""
Simple script to run the NEPSE Trading System
"""
import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from nepse_trading_system import NepseTradingSystem

def main():
    print("="*60)
    print("NEPSE STOCK TRADING & BACKTESTING SYSTEM")
    print("="*60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Quick connectivity check
    print("🔍 Checking system readiness...")
    try:
        from data_fetcher import NepseDataFetcher
        fetcher = NepseDataFetcher()
        
        # Quick API test
        market_status = fetcher.get_market_status()
        if market_status.get('isOpen') != 'UNKNOWN':
            print("✅ API connection: Working")
            api_mode = "LIVE"
        else:
            print("⚠️  API connection: Timeout/Unavailable")
            print("📝 System will run in DEMO MODE with sample data")
            api_mode = "DEMO"
            
    except Exception as e:
        print("⚠️  API connection: Error")
        print("📝 System will run in DEMO MODE with sample data")
        api_mode = "DEMO"
    
    print(f"🚀 Running in {api_mode} MODE")
    print()
    
    try:
        # Initialize and run the system
        system = NepseTradingSystem()
        results = system.run_full_system()
        
        if results:
            print("\n" + "="*60)
            print("🎉 EXECUTION COMPLETED SUCCESSFULLY!")
            print("="*60)
            print(f"📊 Excel file created: {results.get('excel_file', 'N/A')}")
            print(f"🔄 Mode used: {api_mode}")
            print()
            print("📋 The Excel file contains:")
            print("  • Current trading signals (BUY recommendations)")
            print("  • Backtest performance metrics")
            print("  • All historical trades")
            print("  • Portfolio performance history")
            print("  • Company information")
            print("  • Trading rules and configuration")
            print()
            
            if api_mode == "LIVE":
                print("💡 You can now use this data to make informed trading decisions on NEPSE!")
            else:
                print("💡 This is sample data for learning/testing purposes.")
                print("   Try again later when API connectivity improves for live data.")
            
            # Show some key results if available
            if 'backtest_results' in results and 'performance_metrics' in results['backtest_results']:
                metrics = results['backtest_results']['performance_metrics']
                print(f"\n📈 Key Performance Metrics:")
                print(f"   • Total Return: {metrics.get('total_return_percent', 0):.2f}%")
                print(f"   • CAGR: {metrics.get('cagr_percent', 0):.2f}%")
                print(f"   • Win Rate: {metrics.get('win_rate_percent', 0):.2f}%")
                print(f"   • Max Drawdown: {metrics.get('max_drawdown_percent', 0):.2f}%")
                print(f"   • Total Trades: {metrics.get('total_trades', 0)}")
            
            if 'current_signals' in results and not results['current_signals'].empty:
                print(f"\n🎯 Current Buy Signals: {len(results['current_signals'])}")
                for _, signal in results['current_signals'].head(3).iterrows():
                    print(f"   • {signal['symbol']}: Entry NPR {signal['entry_price']:.2f}, Target NPR {signal['target_price']:.2f}")
                if len(results['current_signals']) > 3:
                    print(f"   • ... and {len(results['current_signals']) - 3} more (see Excel file)")
            else:
                print("\n🎯 Current Buy Signals: None at this time")
            
        else:
            print("\n" + "="*60)
            print("❌ EXECUTION FAILED")
            print("="*60)
            print("Please check the error messages above.")
            print("\n🔧 Troubleshooting:")
            print("1. Run: python test_system.py")
            print("2. Check internet connection")
            print("3. Try again in a few minutes")
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Execution interrupted by user.")
        
    except Exception as e:
        print(f"\n\n❌ Unexpected error occurred: {str(e)}")
        print("\n🔧 Troubleshooting:")
        print("1. Run: python test_system.py")
        print("2. Check if all packages are installed: pip install -r requirements.txt")
        print("3. Check internet connection")
        
    finally:
        print(f"\n⏰ Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)

if __name__ == "__main__":
    main()