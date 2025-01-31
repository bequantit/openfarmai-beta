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
