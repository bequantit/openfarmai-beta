# OpenFarma Source Code Directory (`openfarma/src/`)

This directory contains the core application source code for the OpenFarma AI Assistant, providing a comprehensive pharmaceutical assistance system with chat interface, authentication, database management, and AI-powered product recommendations.

## 📁 Directory Structure

```
openfarma/src/
├── README.md           # This documentation file
├── __init__.py         # Package initialization
├── params.py           # Configuration parameters and constants
├── utils.py            # Utility functions and prompt tracking
├── login.py            # Authentication and user management
├── fc.py               # Function calling and vector database operations
└── chat.py             # Main chat interface and conversation management
```

## 🎯 Purpose

The `openfarma/src/` directory serves as the main application layer for the OpenFarma AI Assistant, providing:

- **Authentication System**: User login and session management
- **Chat Interface**: AI-powered conversational interface for pharmaceutical assistance
- **Product Database**: Vector-based search and recommendation system
- **Configuration Management**: Centralized parameter and path management
- **Utility Functions**: Prompt tracking and helper functions

## 📋 Components Overview

### 1. Configuration Management (`params.py`)

**Purpose**: Centralized configuration for all application parameters, paths, and constants.

**Key Features**:
- Database file paths (CSV, Chroma vector databases)
- Google Sheets integration IDs
- Image and asset paths
- Application constants and settings
- Email configuration
- Prompt tracking settings

**Usage**:
```python
from openfarma.src.params import (
    LOGIN_PATH, 
    STOCK_PATH, 
    CHROMA_DB_PATH,
    K_VALUE_SEARCH,
    HEADER_CAPTION
)

# Access configuration values
print(f"Login database: {LOGIN_PATH}")
print(f"Search results limit: {K_VALUE_SEARCH}")
```

**Available Paths**:
- **Database Paths**: Login, stock, stores, images, ABM data
- **Vector Databases**: Chroma DB paths for different product categories
- **Configuration Files**: Assistant config, function calling config, credentials
- **Image Assets**: User/bot avatars, header logo
- **Script Paths**: Data synchronization scripts

**Constants**:
- `K_VALUE_SEARCH`: Number of search results (30)
- `K_VALUE_THOLD`: Threshold for product display (5)
- `STOCK_UPDATE_INTERVAL`: Stock update frequency (3600 seconds)
- `USER_CHAT_COLUMNS`: Chat layout for user messages
- `BOT_CHAT_COLUMNS`: Chat layout for bot messages

### 2. Utility Functions (`utils.py`)

**Purpose**: Provide utility functions for prompt tracking and session management.

**Key Components**:

#### PromptTracker Class
**Purpose**: Track and report user prompt usage for analytics and monitoring.

**Features**:
- Session-based prompt counting
- Time-based reporting intervals
- Google Sheets integration for data storage
- Automatic report generation
- Error handling and logging

**Usage Example**:
```python
from openfarma.src.utils import PromptTracker

# Initialize tracker
tracker = PromptTracker()

# Track user prompts
tracker.incrementPromptCount()

# Manual report generation
tracker.reportPrompts()
```

**Tracking Data**:
- Store ID and name
- Time period (from/to datetime)
- Number of prompts in period
- Automatic reporting every 60 minutes

### 3. Authentication System (`login.py`)

**Purpose**: Handle user authentication and session management for the OpenFarma application.

**Key Components**:

#### LoginNoPassword Class
**Purpose**: Simplified authentication without password requirements.

**Features**:
- Username-only authentication
- Store selection and validation
- Session state management
- Header image rendering
- User data validation

**Usage Example**:
```python
from openfarma.src.login import LoginNoPassword

# Initialize login system
login = LoginNoPassword()

# Render login interface
login.render()
```

#### Login Class
**Purpose**: Full authentication system with password support and recovery.

**Features**:
- Username/password authentication
- Password recovery via email
- Store information management
- Session state initialization
- Email integration for recovery

**Usage Example**:
```python
from openfarma.src.login import Login

# Initialize full login system
login = Login()

# Render login interface
login.render()
```

**Authentication Flow**:
1. User selects username from dropdown
2. System validates user credentials
3. Store information is loaded
4. Session state is initialized
5. User is redirected to chat interface

### 4. Function Calling and Database Operations (`fc.py`)

**Purpose**: Manage vector database operations and provide function calling capabilities for product search and recommendations.

**Key Features**:
- Vector database management (Chroma)
- Product search and retrieval
- Stock and pricing data integration
- Image URL management
- Multi-category product search

**Database Collections**:
- `db_all`: Complete product database
- `db_beneficios`: Benefits-based search
- `db_categoria`: Category-based search
- `db_general`: General product information
- `db_indicaciones`: Usage indications
- `db_uso`: Usage instructions
- `db_propiedades`: Product properties

**Usage Example**:
```python
from openfarma.src.fc import (
    retrieveVectorDB,
    buildProductContext,
    buscar_productos_por_categoria
)

# Search products by category
results = buscar_productos_por_categoria(categoria="cremas")

# Build product context
context = buildProductContext(
    ids=product_ids,
    product_data=vector_results,
    include_images=True
)
```

**Available Search Functions**:
- `buscar_productos()`: General product search
- `buscar_productos_por_presentacion()`: Search by presentation
- `buscar_productos_por_beneficios()`: Search by benefits
- `buscar_productos_por_categoria()`: Search by category
- `buscar_productos_por_indicaciones()`: Search by indications
- `buscar_productos_por_modo_uso()`: Search by usage method
- `buscar_productos_por_propiedades()`: Search by properties
- `buscar_productos_por_problema_y_promocion()`: Search by problem and promotion
- `buscar_productos_por_presentacion_y_tamano()`: Search by presentation and size

**Utility Functions**:
- `contar_marcas()`: Count available brands
- `contar_productos_con_stock()`: Count products with stock
- `contar_productos_en_promocion()`: Count products on promotion
- `listar_marcas()`: List all available brands
- `verificar_marca()`: Verify brand existence

### 5. Chat Interface (`chat.py`)

**Purpose**: Provide a comprehensive chat interface for AI-powered pharmaceutical assistance.

**Key Components**:

#### ChatStyle Class
**Purpose**: Manage CSS styling for the chat interface.

**Features**:
- Custom message styling (user/bot)
- Header layout and branding
- Responsive design
- Streamlit UI customization
- Brand color scheme (#8EA749 green)

**Usage Example**:
```python
from openfarma.src.chat import ChatStyle

# Use default styling
style = ChatStyle()

# Custom styling
custom_style = ChatStyle()
custom_style.style = custom_style.style.replace("#8EA749", "#2E8B57")
```

#### ChatConfig Class
**Purpose**: Configure chat interface appearance and behavior.

**Features**:
- Branding elements (title, caption, logos)
- Avatar configuration
- UI text customization
- File path management
- Default value provision

**Usage Example**:
```python
from openfarma.src.chat import ChatConfig

# Default configuration
config = ChatConfig()

# Custom configuration
custom_config = ChatConfig(
    title="🏥 Hospital Assistant",
    header_caption="Asistente médico virtual",
    input_placeholder="Describa sus síntomas..."
)
```

#### Chat Class
**Purpose**: Main chat interface handler with comprehensive conversation management.

**Features**:
- AI conversation management
- Message streaming and display
- Conversation export (TXT, MD, PDF)
- Email integration
- Prompt tracking integration
- Session state management

**Usage Example**:
```python
from openfarma.src.chat import Chat, ChatConfig, ChatStyle

# Initialize chat interface
config = ChatConfig()
style = ChatStyle()
chat = Chat(
    api_key="your-openai-api-key",
    assistant_id="your-assistant-id",
    config=config,
    style=style
)

# Render chat interface
chat.renderChatInterface()

# Export conversation
chat.exportConversation(format="pdf", metadata={"store": "Store Name"})
```

**Export Formats**:
- **TXT**: Plain text format
- **MD**: Markdown format with formatting
- **PDF**: Professional PDF with headers and metadata

**Email Integration**:
- Send conversations via email
- Support for multiple attachments
- Professional email formatting
- Metadata inclusion

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- OpenAI API key
- Google Sheets API credentials
- Required dependencies (see `requirements.txt`)

### Installation
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Configure API keys in Streamlit secrets
4. Set up Google Sheets integration

### Basic Usage
```python
# Import required modules
from openfarma.src.params import *
from openfarma.src.login import LoginNoPassword
from openfarma.src.chat import Chat, ChatConfig, ChatStyle

# Initialize authentication
login = LoginNoPassword()
login.render()

# Initialize chat interface
config = ChatConfig()
style = ChatStyle()
chat = Chat("your-api-key", "assistant-id", config, style)
chat.renderChatInterface()
```

## 🔧 Development

### Code Structure
- **Modular Design**: Each component has clear responsibilities
- **Type Hints**: Comprehensive type annotations
- **Error Handling**: Robust error management throughout
- **Documentation**: Detailed docstrings and examples

### Database Integration
- **CSV Files**: User data, stock information, store details
- **Chroma Vector DB**: Product information and search capabilities
- **Google Sheets**: Data synchronization and reporting

### Authentication Flow
1. User selection from dropdown
2. Store validation and assignment
3. Session state initialization
4. Redirect to chat interface

### Chat Interface Features
- **Real-time Streaming**: Live AI responses
- **Message History**: Persistent conversation state
- **Export Capabilities**: Multiple format support
- **Prompt Tracking**: Usage analytics and reporting

## 📚 API Reference

### LoginNoPassword Class
- `render()`: Display login interface
- `_verifyUser(username)`: Validate user credentials
- `_setSessionData()`: Initialize session state

### Login Class
- `render()`: Display full login interface
- `_verifyCredentials(username, password)`: Validate credentials
- `_sendRecoveryEmail()`: Send password recovery email

### Chat Class
- `renderChatInterface()`: Display main chat interface
- `processUserInput(user_input)`: Handle user messages
- `exportConversation(format, output_path, metadata)`: Export conversations
- `sendConversationEmail()`: Email conversation export
- `clearChat(report)`: Clear conversation history

### Function Calling (fc.py)
- `retrieveVectorDB(database, context, k)`: Search vector database
- `buildProductContext(ids, product_data, **kwargs)`: Build product context
- `buscar_productos_por_categoria(**kwargs)`: Category-based search
- `retrieveSaleData(ids, file_path, null_stock)`: Get sales data

### PromptTracker Class
- `incrementPromptCount()`: Track user prompts
- `reportPrompts()`: Generate usage report
- `_saveToGoogleSheet(data)`: Save to analytics sheet

## 🐛 Troubleshooting

### Common Issues
1. **Authentication Errors**: Check user database and store configuration
2. **Vector DB Issues**: Verify Chroma database paths and embeddings
3. **API Key Problems**: Ensure OpenAI API key is valid and has credits
4. **Google Sheets Errors**: Check credentials and sheet permissions
5. **Export Failures**: Verify file paths and permissions

### Database Issues
- Verify CSV file paths in `params.py`
- Check Chroma database directory structure
- Validate Google Sheets IDs and permissions
- Ensure proper data formatting in CSV files

## 📄 Configuration

### Environment Variables
- `OPENFARMA_API_KEY`: OpenAI API key
- `EMAIL_FROM`: Sender email address
- `EMAIL_PASSWORD`: Email password
- `GOOGLE_CREDENTIALS`: Google Sheets credentials

### Streamlit Secrets
```toml
[secrets]
OPENFARMA_API_KEY = "your-openai-api-key"
EMAIL_FROM = "sender@example.com"
EMAIL_PASSWORD = "email-password"
EMAIL_TO = "receiver@example.com"

[secrets.credentials]
json = '{"type": "service_account", ...}'
```

---

**Note**: This directory contains the core application logic for the OpenFarma AI Assistant. For the underlying AI infrastructure, see the `src/assistant/` directory in the project root.
