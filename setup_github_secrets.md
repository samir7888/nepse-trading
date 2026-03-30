# GitHub Secrets Setup Guide

To make the automated trading system work, you need to set up these GitHub repository secrets:

## Required Secrets

1. **EMAIL_USER**: Your Gmail address (e.g., `basnetsameer78@gmail.com`)
2. **EMAIL_PASSWORD**: Your Gmail App Password (NOT your regular password)
3. **TO_EMAIL**: Email address to receive reports (can be same as EMAIL_USER)

## How to Set Up Gmail App Password

1. Go to your Google Account settings
2. Navigate to Security → 2-Step Verification (enable if not already)
3. Go to Security → App passwords
4. Generate a new app password for "Mail"
5. Use this 16-character password as EMAIL_PASSWORD

## How to Add Secrets to GitHub

1. Go to your GitHub repository
2. Click Settings → Secrets and variables → Actions
3. Click "New repository secret"
4. Add each secret:
   - Name: `EMAIL_USER`, Value: `your-email@gmail.com`
   - Name: `EMAIL_PASSWORD`, Value: `your-16-char-app-password`
   - Name: `TO_EMAIL`, Value: `recipient@gmail.com`

## Testing the Workflow

After setting up secrets, you can:

1. Go to Actions tab in your GitHub repository
2. Find "NEPSE Trading System" workflow
3. Click "Run workflow" to test manually
4. Check the logs to see if everything works

## Schedule

The workflow is set to run every 2 days at 9:00 AM UTC (2:45 PM Nepal Time).
You can modify the cron schedule in `.github/workflows/trading-system.yml` if needed.

## Troubleshooting

- If emails don't send, check the Action logs for error messages
- Make sure your Gmail account has 2FA enabled and you're using an App Password
- Verify all three secrets are set correctly in GitHub
