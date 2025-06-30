# OpenFarma Assistant - AI Chatbot for Dermocosmetics
---

## Overview
OpenFarma Assistant is a sophisticated AI-powered chatbot platform, specifically designed for OpenFarma's dermocosmetics division. Currently in beta production, this system functions as an intelligent assistant for sales representatives, providing comprehensive product information, inventory management, and real-time expert consultation support.

The platform combines OpenAI's advanced natural language processing capabilities with OpenFarma's extensive dermocosmetics database to deliver accurate and contextualized responses to sales representatives' queries.

- **Secure Authentication**: Specific login system for sales representatives
- **AI-Powered Assistance**: Powered by OpenAI to provide expert knowledge on:
  - Product descriptions and specifications
  - Ingredients and their benefits
  - Application methods and recommendations
  - Contraindications and safety information
- **Real-Time Business Intelligence**:
  - Branch-specific inventory levels
  - Current pricing information
  - Active promotions and discounts
- **Session Management**:
  - Branch-specific data access
  - Automated PDF conversation summary sent via email upon logout

## 📁 Project Structure

```
openfarmai-beta/
├── README.md                    # Project documentation and setup guide
├── requirements.txt             # Python dependencies and versions
├── .gitignore                   # Git ignore patterns
├── .streamlit/                  # Streamlit configuration
│   ├── config.toml             # Streamlit app configuration
│   └── secrets.toml            # Secure API keys and credentials
├── venv/                       # Python virtual environment
├── src/                        # Core AI infrastructure
│   ├── README.md               # AI infrastructure documentation
│   ├── paths.py                # Path configuration utilities
│   └── assistant/              # OpenAI Assistant integration
│       ├── __init__.py         # Package initialization
│       ├── assistant.py        # Assistant creation and management
│       ├── thread.py           # Conversation thread handling
│       └── tools.py            # Function calling and file search
└── openfarma/                  # Main application
    ├── main.py                 # Application entry point
    ├── src/                    # Application source code
    │   ├── README.md           # Application documentation
    │   ├── __init__.py         # Package initialization
    │   ├── params.py           # Configuration parameters
    │   ├── utils.py            # Utility functions
    │   ├── login.py            # Authentication system
    │   ├── fc.py               # Function calling and database ops
    │   └── chat.py             # Chat interface and management
    ├── config/                 # Configuration files
    │   ├── assistant.json      # OpenAI Assistant configuration
    │   ├── fc.json             # Function calling definitions
    │   └── build.py            # Configuration builder
    ├── database/               # Data storage and management
    │   ├── login.csv           # User authentication data
    │   ├── sucursales.csv      # Store/branch information
    │   ├── stock.csv           # Product inventory data
    │   ├── abm.csv             # Product catalog (ABM)
    │   ├── imagenes.csv        # Product images and URLs
    │   ├── openfarma.csv       # Complete product database
    │   ├── build.py            # Database builder
    │   └── chroma/             # Vector database collections
    │       ├── db_all/         # Complete product embeddings
    │       ├── db_Beneficios/  # Benefits-based search
    │       ├── db_Categoria/   # Category-based search
    │       ├── db_General/     # General product info
    │       ├── db_Indicaciones/# Usage indications
    │       ├── db_Modo de uso/ # Usage instructions
    │       └── db_Propiedades/ # Product properties
    ├── images/                 # Application assets
    │   ├── header_logo.png     # Application header logo
    │   ├── avatar_user.png     # User avatar image
    │   └── avatar_bot.png      # Bot avatar image
    ├── history/                # Conversation exports
    │   ├── README.md           # History documentation
    │   └── *.pdf               # Exported conversations
    └── run/                    # Data synchronization scripts
        ├── pull-stock.py       # Download stock data
        ├── push-stock.py       # Upload stock data
        ├── pull-images.py      # Download image data
        ├── push-images.py      # Upload image data
        ├── pull-abm.py         # Download ABM data
        ├── push-abm.py         # Upload ABM data
        └── build-abm-db.py     # Build vector database
```

### 📋 Directory Descriptions

#### **Root Level**
- **`README.md`**: Project documentation, setup instructions, and usage guide
- **`requirements.txt`**: Python package dependencies with specific versions
- **`.gitignore`**: Git ignore patterns for sensitive files and build artifacts
- **`.streamlit/`**: Streamlit framework configuration and secrets management
- **`venv/`**: Python virtual environment for dependency isolation

#### **`src/` - AI Infrastructure**
Core AI capabilities and OpenAI Assistant integration:
- **`assistant/`**: Complete OpenAI Assistant toolkit
  - `assistant.py`: Assistant creation, configuration, and management
  - `thread.py`: Conversation thread handling with streaming capabilities
  - `tools.py`: Function calling and file search/retrieval utilities
- **`paths.py`**: Centralized path configuration for cross-platform compatibility

#### **`openfarma/` - Main Application**
Complete pharmaceutical assistance application:

##### **`src/` - Application Logic**
- **`params.py`**: Centralized configuration (paths, constants, API keys)
- **`login.py`**: Authentication system (password and no-password modes)
- **`chat.py`**: Main chat interface with styling and export capabilities
- **`fc.py`**: Function calling for product search and database operations
- **`utils.py`**: Utility functions including prompt tracking

##### **`config/` - Configuration Files**
- **`assistant.json`**: OpenAI Assistant configuration and instructions
- **`fc.json`**: Function calling definitions for product search
- **`build.py`**: Configuration file builder and validator

##### **`database/` - Data Management**
- **CSV Files**: Structured data storage
  - `login.csv`: User credentials and store assignments
  - `sucursales.csv`: Store/branch information and locations
  - `stock.csv`: Real-time inventory and pricing data
  - `abm.csv`: Product catalog with descriptions and specifications
  - `imagenes.csv`: Product images and URLs
  - `openfarma.csv`: Complete product database
- **`chroma/`**: Vector database collections for semantic search
  - Multiple specialized collections for different search types
  - Enables AI-powered product recommendations

##### **`images/` - Application Assets**
- **`header_logo.png`**: Application branding and header logo
- **`avatar_user.png`**: User avatar for chat interface
- **`avatar_bot.png`**: Bot avatar for AI responses

##### **`history/` - Conversation Management**
- **PDF Exports**: Automated conversation summaries
- **Session Tracking**: User interaction history and analytics

##### **`run/` - Data Synchronization**
- **Pull Scripts**: Download data from external sources (Google Sheets)
- **Push Scripts**: Upload data to external systems
- **Build Scripts**: Database construction and maintenance

### 🔧 Key Components

#### **AI Infrastructure (`src/`)**
- **OpenAI Integration**: Complete Assistant API integration
- **Vector Search**: Chroma-based semantic product search
- **Function Calling**: Dynamic product search and filtering
- **Streaming Responses**: Real-time AI conversation handling

#### **Application Layer (`openfarma/`)**
- **Authentication**: Secure user login and session management
- **Chat Interface**: Professional pharmaceutical assistance UI
- **Data Management**: Real-time inventory and product synchronization
- **Export System**: Conversation summaries and analytics

#### **Data Layer**
- **Structured Data**: CSV files for user, store, and product information
- **Vector Database**: Chroma collections for AI-powered search
- **External Integration**: Google Sheets for data synchronization
- **Configuration**: JSON files for AI assistant and function definitions

## Package Installation
Required packages are listed in the file: *requirements.txt*

- Create virtual environment: `python3.10 -m venv venv`
- Activate virtual environment: `source venv/bin/activate`
- Update pip: `python3.10 -m pip install --upgrade pip`
- Install packages from *requirements.txt*: `pip install -r requirements.txt`
- Uninstall all packages: `pip freeze | xargs pip uninstall -y`
- Deactivate virtual environment: `deactivate`
- Remove virtual environment (optional): `rm -rf venv`

## Local Installation Note
If you are installing OpenFarma Assistant on your personal computer (not deploying to Streamlit Cloud), do not install `pysqlite3-binary` from the requirements.txt file. This package is specifically required for cloud deployment and may conflict with your local SQLite installation.

When installing locally, you can either:
- Remove or comment out `pysqlite3-binary` from requirements.txt before running `pip install -r requirements.txt`
- Or selectively install packages excluding pysqlite3: `pip install -r requirements.txt --exclude pysqlite3-binary`

## Python Version Compatibility
OpenFarma Assistant has been extensively tested and proven to work reliably with Python 3.10. This version provides the optimal balance between stability and feature support for all dependencies used in the project. While the system may work with other Python versions, we strongly recommend using Python 3.10 to ensure consistent behavior and avoid potential compatibility issues.

Key benefits of using Python 3.10 with OpenFarma Assistant:
- Verified compatibility with all required packages
- Stable performance in production environments
- Proven integration with OpenAI and Streamlit components
- Consistent behavior across different operating systems

## 🚀 Quick Start

### Prerequisites
- Python 3.10
- OpenAI API key
- Google Sheets API credentials (for data synchronization)

### Setup Steps
1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd openfarmai-beta
   ```

2. **Create virtual environment**
   ```bash
   python3.10 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure secrets**
   - Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`
   - Add your API keys and credentials

5. **Run the application**
   ```bash
   streamlit run openfarma/main.py
   ```

## 📚 Documentation

- **`src/README.md`**: AI infrastructure documentation
- **`openfarma/src/README.md`**: Application layer documentation
- **`openfarma/main.py`**: Main application entry point with detailed comments
- **`openfarma/history/README.md`**: Conversation export documentation

## Notes
- If you already have __pycache__ directories that you want to remove, you can use this command:
  ```
  find . -type d -name __pycache__ -exec rm -rf {} +
  ```
- To prevent Python from creating `__pycache__` directories when running your script, you can use the `-B` flag (or the environment variable `PYTHONDONTWRITEBYTECODE=1`). Here's how to modify your command:
  ```
  python3.10 -B -m folder.file
  ```
