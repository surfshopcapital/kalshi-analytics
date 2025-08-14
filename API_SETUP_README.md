# 🔐 Kalshi API Key Setup Guide

This guide will help you securely configure your Kalshi API credentials for the Portfolio Dashboard.

## 🚨 Security First

**NEVER commit API keys or private keys to version control!** The setup process creates a `.gitignore` file to prevent accidental commits of sensitive information.

## 📋 Prerequisites

1. **Kalshi Account**: You need an active Kalshi trading account
2. **API Access**: API access enabled in your Kalshi account
3. **Two Key Pieces**:
   - **API Key ID**: A UUID-like string (e.g., `00000000-0000-0000-0000-000000000000`)
   - **Private Key**: PEM-formatted private key for RSA signature authentication

## 🔑 Getting Your Kalshi API Credentials

### Step 1: Access Kalshi API Settings
1. Log into your Kalshi account
2. Go to **Account Settings** → **API Keys**
3. Click **Generate New API Key**

### Step 2: Save Your Credentials
1. **Copy the API Key ID** (this is NOT the private key)
2. **Download the Private Key** (PEM format)
3. **Store both securely** - you won't be able to see the private key again

## 🚀 Quick Setup (Recommended)

### Option 1: Automated Setup Script
```bash
python setup_api_keys.py
```

The script will:
- Prompt for your API Key ID
- Prompt for your Private Key (PEM format)
- Create `config.py` with your credentials
- Create/update `.gitignore` for security
- Test the configuration

### Option 2: Manual Setup

1. **Create `config.py`**:
```python
# config.py - Kalshi API Configuration
# ⚠️  IMPORTANT: Never commit this file to version control!

# Your Kalshi API Key ID
KALSHI_API_KEY_ID = "your_api_key_id_here"

# Your Kalshi Private Key (PEM format)
KALSHI_PRIVATE_KEY = """-----BEGIN PRIVATE KEY-----
MIIEpAIBAKCAQEA...
... your full private key content ...
-----END PRIVATE KEY-----"""

# Alternative: Store private key in a separate file
KALSHI_PRIVATE_KEY_PATH = "kalshi_private_key.pem"

# API Configuration
KALSHI_BASE_URL = "https://trading-api.kalshi.com"
KALSHI_SANDBOX_URL = "https://sandbox-api.kalshi.com"
```

2. **Create `.gitignore`** (if not exists):
```gitignore
# Environment variables and configuration
.env
config.py
kalshi_private_key.pem
*.pem
*.key

# API Keys and secrets
secrets.json
credentials.json
api_keys.txt
```

## 🔍 Verification

### Test Your Configuration
1. Run the JKB Portfolio Dashboard
2. Check the "🔧 API Key Configuration Help" section
3. Click "📁 View Current Configuration Status"
4. Verify both API Key ID and Private Key are loaded

### Expected Results
- ✅ Configuration loaded successfully
- ✅ API Key ID: `xxxxxxxx-...-xxxx`
- ✅ Private Key: `[X] characters`
- ✅ Status: Ready for portfolio access

## 🛠️ Troubleshooting

### Common Issues

#### 1. "Configuration not found"
- **Solution**: Run `python setup_api_keys.py` or create `config.py` manually
- **Check**: Ensure `config.py` exists in your project root

#### 2. "Private Key format error"
- **Solution**: Ensure your private key starts with `-----BEGIN PRIVATE KEY-----`
- **Check**: Copy the entire key including BEGIN/END lines

#### 3. "Import Error"
- **Solution**: Check Python path and file permissions
- **Check**: Ensure `config.py` is in the same directory as your main script

#### 4. Portfolio endpoints still failing
- **Solution**: Verify your private key is correct and in PEM format
- **Check**: Use the API Connection Test section in the JKB dashboard

### Debug Steps
1. **Check terminal output** for detailed error messages
2. **Verify file permissions** (especially on Unix systems)
3. **Test with simple API calls** first (markets endpoint)
4. **Check Kalshi account** for API access status

## 🔒 Security Best Practices

### ✅ Do's
- Use environment variables in production
- Store private keys in secure key management services
- Regularly rotate API keys
- Use separate keys for development/production
- Monitor API usage and set rate limits

### ❌ Don'ts
- Never commit `config.py` to version control
- Don't share private keys in chat/email
- Don't use the same key across multiple applications
- Don't store keys in plain text files
- Don't log API keys to console/logs

## 📁 File Structure After Setup

```
your_project/
├── config.py              # 🔐 Your API credentials (NOT committed)
├── .gitignore            # 🛡️  Protects sensitive files
├── setup_api_keys.py     # 🚀 Setup automation script
├── kalshi_client.py      # 🔌 API client implementation
├── pages/
│   └── JKB.py           # 📊 Portfolio dashboard
└── utils.py              # 🛠️  Utility functions
```

## 🎯 Next Steps

After successful setup:
1. **Test the JKB Portfolio Dashboard**
2. **Verify portfolio data loads correctly**
3. **Check all portfolio endpoints work**
4. **Monitor for any authentication errors**

## 🆘 Need Help?

If you encounter issues:
1. Check the troubleshooting section above
2. Review terminal/console output for error messages
3. Verify your Kalshi account API access
4. Ensure your private key is in the correct PEM format

---

**Remember**: Your API credentials give access to your trading account. Keep them secure and never share them publicly!
