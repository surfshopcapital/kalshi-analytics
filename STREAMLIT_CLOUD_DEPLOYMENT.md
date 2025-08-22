# Streamlit Cloud Deployment Guide

This guide explains how to deploy your Market Dashboards application to Streamlit Cloud and fix the import issues.

## Problem Description

When running locally, the application works fine because Python can find the local modules. However, on Streamlit Cloud, the Python path doesn't include the project root directory, causing import errors like:

```
KeyError: 'utils'
```

## Solution Implemented

### 1. Import Helper (`import_helper.py`)

Created a comprehensive import helper that:
- Adds the project root to Python path
- Handles Streamlit Cloud's `/mount/src/` directory structure
- Provides fallback import methods
- Gives detailed debug information

### 2. Updated All Page Files

Modified all page files in the `pages/` directory to:
- Import the `import_helper` module first
- Use proper import paths
- Handle import failures gracefully

### 3. Streamlit Configuration

Created proper Streamlit configuration files:
- `.streamlit/config.toml` - Main configuration
- `.streamlit/secrets.toml` - Secrets template
- `packages.txt` - System dependencies

### 4. Package Structure

Added proper Python package structure:
- `__init__.py` files in root and pages directories
- `setup.py` for package installation
- `streamlit_app.py` as main entry point

## Files Modified

### Core Files
- `Dashboard.py` - Added main function and import helper
- `import_helper.py` - New comprehensive import helper
- `streamlit_app.py` - New main entry point

### Page Files
- `pages/Decay.py` - Updated imports
- `pages/JKB.py` - Updated imports
- `pages/Markets.py` - Updated imports
- `pages/Overview.py` - Updated imports
- `pages/Movers.py` - Updated imports
- `pages/Series.py` - Updated imports

### Configuration Files
- `.streamlit/config.toml` - Streamlit configuration
- `.streamlit/secrets.toml` - Secrets template
- `packages.txt` - System dependencies
- `setup.py` - Package setup
- `__init__.py` - Package markers

## How It Works

1. **Import Helper**: When any page loads, `import_helper.py` runs first and sets up the Python path
2. **Path Resolution**: The helper adds multiple possible paths including Streamlit Cloud's mount directories
3. **Fallback Imports**: If direct imports fail, the helper tries alternative import methods
4. **Debug Information**: Detailed logging shows what's happening during import

## Deployment Steps

### 1. Push to GitHub
```bash
git add .
git commit -m "Fix Streamlit Cloud import issues"
git push origin main
```

### 2. Connect to Streamlit Cloud
- Go to [share.streamlit.io](https://share.streamlit.io)
- Connect your GitHub repository
- Set the main file path to `streamlit_app.py`

### 3. Configure Secrets
- In Streamlit Cloud, go to your app settings
- Add the secrets from `.streamlit/secrets.toml`
- Set the actual API keys and configuration values

### 4. Deploy
- Streamlit Cloud will automatically deploy your app
- Check the logs for import status messages
- The import helper will show detailed debug information

## Testing Locally

To test the import fixes locally:

```bash
python test_imports.py
```

This will verify that all modules can be imported correctly.

## Troubleshooting

### Import Still Fails
1. Check the Streamlit Cloud logs for debug messages
2. Verify the import helper is running
3. Check if the mount paths exist on Streamlit Cloud

### Module Not Found
1. Ensure all `__init__.py` files are present
2. Check that the import helper is imported first
3. Verify the file structure matches the expected layout

### Streamlit Configuration Issues
1. Check `.streamlit/config.toml` syntax
2. Verify secrets are properly configured
3. Ensure `packages.txt` contains required system packages

## Expected Behavior

After deployment:
1. Import helper runs and sets up paths
2. All page imports succeed
3. Dashboard loads without import errors
4. Debug messages show successful imports

## Monitoring

Watch the Streamlit Cloud logs for:
- ✅ Successfully imported utils module
- ✅ Successfully imported shared_sidebar module
- ✅ Successfully imported kalshi_client module
- ✅ Successfully imported polymarket_client module

If you see ❌ messages, the import helper will provide detailed error information to help debug the issue.
