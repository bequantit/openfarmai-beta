# OpenFarma Assistant - Dermocosmetics AI Chatbot
---

## Overview
OpenFarma Assistant is a sophisticated AI-powered chatbot platform specifically designed for OpenFarma's dermocosmetics division. Currently in beta production, this system serves as an intelligent assistant for sales representatives, providing comprehensive product information, inventory management, and expert consultation support in real-time.

The platform combines advanced natural language processing capabilities powered by OpenAI with OpenFarma's extensive dermocosmetics database to deliver accurate, context-aware responses to sales representative inquiries.

- **Secure Authentication**: User-specific login system for sales representatives
- **AI-Powered Assistance**: Powered by OpenAI to provide expert knowledge about:
  - Product descriptions and specifications
  - Ingredients and their benefits
  - Application methods and recommendations
  - Contraindications and safety information
- **Real-time Business Intelligence**:
  - Branch-specific inventory levels
  - Current pricing information
  - Active promotions and discounts
- **Session Management**:
  - Branch-specific data access
  - Automated PDF conversation summary sent via email upon logout

## Package Installation
The necessary packages are listed in the file: *requirements.txt*

- Create the virtual environment: `python3.10 -m venv venv`
- Activate the virtual environment: `source venv/bin/activate`
- Upgrade pip: `python3.10 -m pip install --upgrade pip`
- Install packages from *requirements.txt*: `pip install -r requirements.txt`
- Uninstall all packages: `pip freeze | xargs pip uninstall -y`
- Deactivate the virtual environment: `deactivate`
- Remove the virtual environment (optional): `rm -rf venv`

## Local Installation Note
If you are installing OpenFarma Assistant on your personal computer (not deploying to Streamlit Cloud), do not install `pysqlite3-binary` from the requirements.txt file. This package is specifically required for cloud deployment and may conflict with your local SQLite installation.

When installing locally, you can either:
- Remove `pysqlite3-binary` from requirements.txt before running `pip install -r requirements.txt`
- Or selectively install packages excluding pysqlite3: `pip install -r requirements.txt --exclude pysqlite3-binary`

## Python Version Compatibility
OpenFarma Assistant has been extensively tested and proven to work reliably with Python 3.10. This version provides the optimal balance of stability and feature support for all dependencies used in the project. While the system may work with other Python versions, we strongly recommend using Python 3.10 to ensure consistent behavior and avoid potential compatibility issues.

Key benefits of using Python 3.10 with OpenFarma Assistant:
- Verified compatibility with all required packages
- Stable performance in production environments
- Tested integration with OpenAI and Streamlit components
- Consistent behavior across different operating systems


## Organization


## Notes
- If you already have __pycache__ directories that you want to remove, you can use this command:
  ```
  find . -type d -name __pycache__ -exec rm -rf {} +
  ```
- To prevent Python from creating `__pycache__` directories when running your script, you can use the `-B` flag (or `PYTHONDONTWRITEBYTECODE=1` environment variable). Here's how to modify your command:
  ```
  python3.10 -B -m folder.file
  ```
