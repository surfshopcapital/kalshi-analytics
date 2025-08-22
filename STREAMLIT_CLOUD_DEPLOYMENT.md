# Streamlit Cloud Deployment Guide

## Overview
This guide explains how to deploy your Market Dashboards application to Streamlit Cloud with proper API key configuration.

## Prerequisites
- GitHub repository with your code
- Streamlit Cloud account
- Kalshi API credentials (API Key ID and Private Key)

## Deployment Steps

### 1. Repository Setup
Ensure your repository has the following files:
- `streamlit_app.py` (main entry point)
- `requirements.txt` (Python dependencies)
- `packages.txt` (system packages - can be empty)
- `.gitignore` (excludes config.py and private keys)
- `kalshi_private_key.pem` (your private key file - **IMPORTANT: This should NOT be committed to git**)

### 2. API Key Configuration for Streamlit Cloud

#### Option A: Private Key File (Recommended for Security)
1. **Create your private key file locally:**
   - Create `kalshi_private_key.pem` in your project root
   - Paste your private key content (PEM format)
   - Ensure the file is in `.gitignore` (already done)

2. **Set environment variables in Streamlit Cloud:**
   - Go to your Streamlit Cloud app settings
   - Navigate to "Secrets" section
   - Add the following secrets:

```toml
[KALSHI_API_KEY_ID]
"your_api_key_id_here"

[KALSHI_PRIVATE_KEY_PATH]
"kalshi_private_key.pem"
```

3. **Upload your private key file:**
   - In Streamlit Cloud, go to "Files" section
   - Upload your `kalshi_private_key.pem` file
   - This keeps your private key secure and separate from code

#### Option B: Environment Variables (Alternative)
If you prefer to use environment variables directly:

```toml
[KALSHI_API_KEY_ID]
"your_api_key_id_here"

[KALSHI_PRIVATE_KEY]
"-----BEGIN RSA PRIVATE KEY-----
your_private_key_content_here
-----END RSA PRIVATE KEY-----"
```

### 3. Deploy to Streamlit Cloud
1. Connect your GitHub repository
2. Set the main file path to `streamlit_app.py`
3. Deploy the app

## Troubleshooting

### Common Issues

#### 1. "Unable to locate package packages" Error
This error typically occurs when:
- There are hidden characters in `packages.txt`
- The file is corrupted during upload
- Streamlit Cloud has parsing issues

**Solution:**
- Ensure `packages.txt` is clean and contains only comments
- Try recreating the file with simple content
- Check for any hidden characters or encoding issues

#### 2. Portfolio Data Not Loading
**Symptoms:**
- JKB page shows "No portfolio data available"
- Authentication status shows missing private key

**Solutions:**
1. **For file-based approach:** Ensure `kalshi_private_key.pem` is uploaded to Streamlit Cloud
2. **For environment variables:** Verify both API Key ID and Private Key are set correctly
3. Check that the private key format is correct (PEM format)
4. Ensure both API Key ID and Private Key are provided

#### 3. Authentication Errors
**Common causes:**
- Private key format incorrect
- Missing environment variables
- Private key file not uploaded to Streamlit Cloud
- Incorrect API endpoint URLs

**Debugging:**
- Check the authentication status display on the JKB page
- Verify environment variable values in Streamlit Cloud
- Ensure private key file is uploaded if using file-based approach
- Test API connectivity with simple endpoints first

### Debug Information
The JKB page includes a debug section that shows:
- API key presence
- Private key format validation
- Environment variable status
- Authentication method being used

## Security Best Practices

### 1. Never Commit Sensitive Data
- Keep `config.py` in `.gitignore`
- Keep `kalshi_private_key.pem` in `.gitignore`
- Use environment variables for production
- Avoid hardcoding API keys in source code

### 2. Streamlit Cloud Security
- Use Streamlit's built-in secrets management
- Upload private key files securely
- Rotate API keys regularly
- Monitor API usage and costs

### 3. API Key Management
- Use separate API keys for development and production
- Implement proper access controls
- Monitor API usage patterns

## Testing Your Deployment

### 1. Local Testing
```bash
# Test with private key file
# Ensure kalshi_private_key.pem exists in project root
streamlit run streamlit_app.py

# Test with environment variables
export KALSHI_API_KEY_ID="your_key_id"
export KALSHI_PRIVATE_KEY_PATH="kalshi_private_key.pem"
streamlit run streamlit_app.py
```

### 2. Cloud Testing
- Deploy to Streamlit Cloud
- Check authentication status on JKB page
- Test portfolio data loading
- Verify error handling works correctly

## Support

If you encounter issues:
1. Check the authentication status on the JKB page
2. Verify environment variables in Streamlit Cloud
3. Ensure private key file is uploaded if using file-based approach
4. Check the Streamlit Cloud logs for errors
5. Ensure your API keys are valid and active

## File Structure
```
Market_Dashboards/
├── streamlit_app.py          # Main entry point
├── requirements.txt          # Python dependencies
├── packages.txt             # System packages (can be empty)
├── .streamlit/              # Streamlit configuration
│   └── secrets.toml        # Local secrets (optional)
├── config.py               # Local configuration (gitignored)
├── kalshi_private_key.pem  # Private key file (gitignored)
├── .gitignore              # Excludes sensitive files
└── pages/                  # Streamlit pages
    └── JKB.py             # Portfolio dashboard
```
