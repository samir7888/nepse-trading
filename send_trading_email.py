#!/usr/bin/env python3
"""
Enhanced email sender for NEPSE Trading System
Formats output in the requested style and sends via Gmail
"""
import smtplib
import os
import sys
import pandas as pd
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
import subprocess
import json
from pathlib import Path

def run_trading_system():
    """Run the trading system and capture output"""
    try:
        # Start backend server
        print("Starting backend server...")
        backend_process = subprocess.Popen([
            sys.executable, "start_backend.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Give server time to start
        import time
        time.sleep(15)
        
        # Run trading system
        print("Running trading system...")
        result = subprocess.run([
            sys.executable, "beginner_trading_system.py"
        ], capture_output=True, text=True, timeout=300)
        
        # Stop backend server
        try:
            backend_process.terminate()
            backend_process.wait(timeout=10)
        except:
            backend_process.kill()
        
        return result.stdout, result.stderr, result.returncode
        
    except Exception as e:
        print(f"Error running trading system: {e}")
        return "", str(e), 1

def parse_excel_output():
    """Parse the Excel output to get trading recommendations"""
    excel_file = "output/beginner_trading_strategy.xlsx"
    
    if not os.path.exists(excel_file):
        return None
    
    try:
        # Read the recommendations sheet
        df = pd.read_excel(excel_file, sheet_name='Investment_Recommendations')
        
        if df.empty or 'Message' in df.columns:
            return None
            
        return df
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return None

def format_trading_email(recommendations_df, capital=20000):
    """Format the trading recommendations in the requested style"""
    
    if recommendations_df is None or recommendations_df.empty:
        return f"""
💰 Your Investment Budget: NPR {capital:,}

📈 CURRENT INVESTMENT OPPORTUNITIES: 0
--------------------------------------------------

❌ No suitable investment opportunities found at this time.

📊 Market Analysis:
• The system analyzed multiple stocks but found no opportunities meeting our strict criteria
• This is normal and shows the system is being conservative with your capital
• We'll continue monitoring and will notify you when good opportunities arise

💡 Next Steps:
• Keep your capital ready for when opportunities emerge
• The system will run again in 2 days
• Consider this a good time to study market trends

🔄 System will check again in 2 days for new opportunities.
        """
    
    # Count opportunities
    num_opportunities = len(recommendations_df)
    
    # Start building the email
    email_content = f"""💰 Your Investment Budget: NPR {capital:,}

📈 CURRENT INVESTMENT OPPORTUNITIES: {num_opportunities}
--------------------------------------------------

"""
    
    # Add each recommendation
    for i, (_, row) in enumerate(recommendations_df.iterrows(), 1):
        symbol = row.get('symbol', 'N/A')
        company_name = row.get('company_name', 'Unknown Company')
        buy_price = row.get('entry_price', 0)
        investment = row.get('recommended_investment', 0)
        target_price = row.get('target_price', 0)
        stop_loss = row.get('stop_loss', 0)
        potential_profit = row.get('potential_profit_npr', 0)
        
        email_content += f"""{i}. {symbol} ({company_name})
💵 Buy Price: NPR {buy_price:.2f}
📊 Recommended Investment: NPR {investment:.0f}
🎯 Target Price: NPR {target_price:.2f}
🛡️  Stop Loss: NPR {stop_loss:.2f}
💡 Potential Profit: NPR {potential_profit:.0f}

"""
    
    # Add summary and disclaimer
    total_investment = recommendations_df['recommended_investment'].sum()
    total_potential_profit = recommendations_df['potential_profit_npr'].sum()
    
    email_content += f"""📊 INVESTMENT SUMMARY:
--------------------------------------------------
💰 Total Recommended Investment: NPR {total_investment:.0f}
💵 Remaining Cash: NPR {capital - total_investment:.0f}
🎯 Total Potential Profit: NPR {total_potential_profit:.0f}
📈 Expected Return: {(total_potential_profit/total_investment)*100:.1f}%

⚠️  IMPORTANT DISCLAIMERS:
• This is an automated analysis system, not financial advice
• Always do your own research before investing
• Never invest more than you can afford to lose
• Past performance doesn't guarantee future results
• Consider consulting a financial advisor

🔄 Next analysis will be sent in 2 days.
📅 Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    return email_content

def send_email(subject, body, attachment_path=None):
    """Send email via Gmail SMTP"""
    
    # Get email credentials from environment variables
    email_user = os.getenv('EMAIL_USER')
    email_password = os.getenv('EMAIL_PASSWORD') 
    to_email = os.getenv('TO_EMAIL')
    
    if not all([email_user, email_password, to_email]):
        print("❌ Email credentials not found in environment variables")
        print("Required: EMAIL_USER, EMAIL_PASSWORD, TO_EMAIL")
        return False
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = email_user
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Add body
        msg.attach(MIMEText(body, 'plain'))
        
        # Add attachment if provided
        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, "rb") as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
                
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {os.path.basename(attachment_path)}'
            )
            msg.attach(part)
        
        # Send email
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(email_user, email_password)
        text = msg.as_string()
        server.sendmail(email_user, to_email, text)
        server.quit()
        
        print("✅ Email sent successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False

def main():
    """Main function to run trading system and send email"""
    print("🚀 Starting NEPSE Trading System Email Service...")
    
    # Run the trading system
    stdout, stderr, returncode = run_trading_system()
    
    # Parse results
    recommendations = parse_excel_output()
    
    # Get capital from config
    try:
        from config import INVESTMENT_CAPITAL
        capital = INVESTMENT_CAPITAL['total_budget']
    except:
        capital = 20000  # Default
    
    # Format email content
    email_body = format_trading_email(recommendations, capital)
    
    # Create subject
    if recommendations is not None and not recommendations.empty:
        num_opportunities = len(recommendations)
        subject = f"📈 NEPSE Trading Alert: {num_opportunities} Investment Opportunities Found!"
    else:
        subject = "📊 NEPSE Trading Update: No Opportunities Today"
    
    # Add system output to email if there were errors
    if returncode != 0 or stderr:
        email_body += f"""

🔧 SYSTEM OUTPUT:
--------------------------------------------------
Return Code: {returncode}

STDOUT:
{stdout[:1000]}...

STDERR:
{stderr[:500]}...
"""
    
    # Send email
    excel_file = "output/beginner_trading_strategy.xlsx" if os.path.exists("output/beginner_trading_strategy.xlsx") else None
    
    success = send_email(subject, email_body, excel_file)
    
    if success:
        print("✅ Trading system completed and email sent!")
    else:
        print("❌ Trading system completed but email failed!")
        print("Email content would have been:")
        print(email_body)

if __name__ == "__main__":
    main()