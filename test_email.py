#!/usr/bin/env python3
"""
Test script to verify email functionality
Run this locally to test your email setup before deploying to GitHub Actions
"""
import os
import pandas as pd
from send_trading_email import format_trading_email, send_email

def create_sample_data():
    """Create sample trading data for testing"""
    sample_data = {
        'symbol': ['SHIVM', 'RIDI', 'NGPL'],
        'company_name': ['Shivam Cements Limited', 'Ridi Power Company Limited', 'Ngadi Group Power Ltd.'],
        'entry_price': [676.00, 380.00, 470.00],
        'recommended_investment': [6760, 3800, 4700],
        'target_price': [1081.60, 608.00, 752.00],
        'stop_loss': [473.20, 266.00, 329.00],
        'potential_profit_npr': [4056, 2280, 2820]
    }
    return pd.DataFrame(sample_data)

def main():
    print("🧪 Testing NEPSE Trading Email System...")
    
    # Check if environment variables are set
    email_user = os.getenv('EMAIL_USER')
    email_password = os.getenv('EMAIL_PASSWORD')
    to_email = os.getenv('TO_EMAIL')
    
    if not all([email_user, email_password, to_email]):
        print("❌ Please set environment variables first:")
        print("   export EMAIL_USER='your-email@gmail.com'")
        print("   export EMAIL_PASSWORD='your-app-password'")
        print("   export TO_EMAIL='recipient@gmail.com'")
        return
    
    print(f"📧 Email User: {email_user}")
    print(f"📧 To Email: {to_email}")
    print(f"🔑 Password: {'*' * len(email_password)}")
    
    # Create sample data
    sample_df = create_sample_data()
    
    # Format email
    email_body = format_trading_email(sample_df, capital=20000)
    
    print("\n📝 Email Content Preview:")
    print("=" * 50)
    print(email_body[:500] + "...")
    print("=" * 50)
    
    # Ask for confirmation
    response = input("\n📤 Send test email? (y/n): ")
    
    if response.lower() == 'y':
        subject = "🧪 TEST: NEPSE Trading System Email"
        success = send_email(subject, email_body)
        
        if success:
            print("✅ Test email sent successfully!")
            print("Check your inbox to verify the format.")
        else:
            print("❌ Test email failed!")
    else:
        print("📧 Test cancelled.")

if __name__ == "__main__":
    main()