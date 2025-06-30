# Source Code Directory (`src/`)

This directory contains the core source code for the OpenFarmAI project, providing essential utilities and modules for OpenAI Assistant integration, path management, and development tools.

## 📁 Directory Structure

```
src/
├── README.md           # This documentation file
├── paths.py           # Path configuration and management utilities
└── assistant/         # OpenAI Assistant integration modules
    ├── __init__.py    # Package initialization
    ├── assistant.py   # Assistant creation and management
    ├── thread.py      # Conversation thread management
    └── tools.py       # Function calling and file search utilities
```

## 🎯 Purpose

The `src/` directory serves as the main source code repository for the OpenFarmAI project, providing:

- **Path Management**: Centralized configuration for project paths and directories
- **OpenAI Integration**: Complete toolkit for creating and managing OpenAI Assistants
- **Conversation Management**: Advanced thread handling with streaming capabilities
- **Tool Integration**: Function calling and file search capabilities for assistants

## 📋 Components Overview

### 1. Path Management (`paths.py`)

**Purpose**: Centralized path configuration for the entire project.

**Key Features**:
- Defines root directory and subdirectory paths
- Provides consistent path references across the application
- Supports cross-platform compatibility

**Usage**:
```python
from src.paths import ROOT, ASSISTANT, OPENFARMA

# Access project directories
print(f"Project root: {ROOT}")
print(f"Assistant module: {ASSISTANT}")
print(f"OpenFarma module: {OPENFARMA}")
```

**Available Paths**:
- `ROOT`: Project root directory
- `DOCS`: Documentation directory
- `IMAGES`: Image assets directory
- `SOURCE`: Source code directory
- `STREAMLIT`: Streamlit configuration directory
- `ASSISTANT`: Assistant module directory
- `OPENFARMA`: OpenFarma module directory

### 2. Assistant Module (`assistant/`)

The assistant module provides comprehensive tools for OpenAI Assistant integration, including creation, management, and advanced features.

#### 2.1 Assistant Management (`assistant.py`)

**Purpose**: Create and configure OpenAI Assistants with advanced capabilities.

**Key Features**:
- Assistant creation with custom metadata
- Model selection and configuration
- Tool integration (code interpreter, retrieval, function calling)
- Temperature and response format control
- Import/export assistant configurations

**Usage Example**:
```python
from src.assistant.assistant import Assistant

# Create a new assistant
assistant = Assistant("your-openai-api-key")

# Configure assistant
assistant.setMetadata(
    name="Math Tutor",
    description="A helpful math tutor that solves complex problems",
    instructions="You are a math tutor. Help students solve problems step by step."
)

# Set model and tools
assistant.setModel("gpt-4-turbo-preview")
assistant.addTool("code_interpreter")

# Create the assistant
response = assistant.create()
print(f"Assistant created with ID: {response.id}")
```

**Supported Tools**:
- `code_interpreter`: Python code execution for calculations
- `retrieval`: File search and document access
- `function`: Custom function calling capabilities

#### 2.2 Thread Management (`thread.py`)

**Purpose**: Manage conversation threads with streaming capabilities and real-time UI updates.

**Key Features**:
- Message queuing and processing
- Streaming responses with real-time updates
- Tool call handling and execution
- Streamlit integration for chat interfaces
- Thread lifecycle management

**Usage Example**:
```python
from src.assistant.thread import Thread

# Create a thread
thread = Thread("your-openai-api-key")

# Add user message
thread.addMessage("Solve the equation: 2x + 5 = 13")

# Define tool handlers
tool_handlers = {
    "calculate": lambda expression: eval(expression)
}

# Run assistant with streaming
thread.runWithStreaming("assistant-id", tool_handlers)
```

**Advanced Features**:
- **Streaming**: Real-time message streaming with UI updates
- **Tool Integration**: Automatic tool call execution
- **Message Queuing**: Batch message processing
- **State Management**: Thread state persistence and retrieval

#### 2.3 Tools and Utilities (`tools.py`)

**Purpose**: Provide function calling capabilities and file search/retrieval for assistants.

**Key Components**:

##### FunctionCalling Class
**Purpose**: Create and deploy custom functions for OpenAI Assistants.

**Features**:
- Fluent API for function definition
- Parameter validation and type checking
- Nested object support
- JSON import/export
- Comprehensive error handling

**Usage Example**:
```python
from src.assistant.tools import FunctionCalling

# Create function calling instance
fc = FunctionCalling("your-openai-api-key")

# Define function metadata
fc.setFunctionMetadata(
    name="get_weather",
    description="Get weather information for a location"
)

# Add parameters
fc.addFunctionParameter(
    name="city",
    param_type="string",
    description="City name",
    required=True
)

fc.addFunctionParameter(
    name="units",
    param_type="string",
    description="Temperature units",
    enum=["celsius", "fahrenheit"]
)

# Create function in assistant
fc.createFunction("assistant-id")
```

**Supported Parameter Types**:
- `string`: Text values with optional enum constraints
- `integer`: Whole numbers
- `number`: Decimal numbers
- `boolean`: True/false values
- `array`: Lists with defined item types
- `object`: Complex objects with nested properties
- `null`: Null values

##### FileSearch Class
**Purpose**: Manage file uploads and vector store creation for document retrieval.

**Features**:
- Support for 20+ file types (PDF, DOCX, TXT, MD, JSON, code files)
- Automatic MIME type detection
- Character encoding validation
- Batch file upload with progress monitoring
- Vector store lifecycle management

**Usage Example**:
```python
from src.assistant.tools import FileSearch

# Create file search instance
fs = FileSearch("your-openai-api-key", "Document Store")

# Upload files
file_paths = ["document1.pdf", "report.docx", "data.json"]
fs.uploadFileBatch(file_paths)

# Attach to assistant
fs.attachVectorStoreToAssistant("assistant-id")
```

**Supported File Types**:
- **Documents**: PDF, DOC, DOCX, PPTX
- **Text**: TXT, MD, HTML, CSS, JSON
- **Code**: PY, JS, TS, JAVA, CPP, CS, GO, PHP, RB, SH
- **Data**: TEX, C, C++

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- OpenAI API key
- Required dependencies (see `requirements.txt`)

### Installation
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set your OpenAI API key as an environment variable

### Basic Usage
```python
# Import required modules
from src.paths import ROOT
from src.assistant.assistant import Assistant
from src.assistant.thread import Thread

# Create an assistant
assistant = Assistant("your-api-key")
assistant.setMetadata("My Assistant", "A helpful assistant", "You are helpful.")
assistant.setModel("gpt-4-turbo-preview")
response = assistant.create()

# Create a thread and start conversation
thread = Thread("your-api-key")
thread.addMessage("Hello!")
thread.runWithStreaming(response.id, {})
```

## 🔧 Development

### Code Structure
- **Modular Design**: Each component is self-contained with clear responsibilities
- **Type Hints**: Comprehensive type annotations for better IDE support
- **Documentation**: Detailed docstrings and examples
- **Error Handling**: Robust error handling with informative messages

### Testing
- Each module includes comprehensive error handling
- Examples provided in docstrings for testing
- Modular design allows for unit testing of individual components

### Contributing
1. Follow the existing code structure and patterns
2. Add comprehensive docstrings for new functions
3. Include usage examples in docstrings
4. Test your changes thoroughly
5. Update this README if adding new features

## 📚 API Reference

### Assistant Class
- `setMetadata(name, description, instructions)`: Configure assistant metadata
- `setModel(model)`: Set the AI model
- `addTool(tool_type, function=None)`: Add tools to assistant
- `create()`: Create the assistant in OpenAI
- `importFromFile(file_path)`: Import configuration from JSON

### Thread Class
- `addMessage(content, role="user")`: Add message to thread
- `runWithStreaming(assistant_id, tool_handlers)`: Run with real-time streaming
- `runWithoutStreaming(assistant_id, tool_handlers)`: Run without streaming
- `listMessages(limit=20)`: Retrieve thread messages
- `delete()`: Delete the thread

### FunctionCalling Class
- `setFunctionMetadata(name, description)`: Set function metadata
- `addFunctionParameter(name, type, description, required=False)`: Add parameters
- `createFunction(assistant_id)`: Deploy function to assistant
- `importFromFile(file_path)`: Import function definition

### FileSearch Class
- `uploadFileBatch(file_paths)`: Upload multiple files
- `attachVectorStoreToAssistant(assistant_id)`: Attach to assistant
- `getVectorStoreStatus()`: Check upload status
- `deleteVectorStore()`: Clean up vector store

## 🐛 Troubleshooting

### Common Issues
1. **API Key Errors**: Ensure your OpenAI API key is valid and has sufficient credits
2. **File Upload Issues**: Check file types and sizes are supported
3. **Tool Call Errors**: Verify tool handlers are properly defined
4. **Streaming Issues**: Check network connectivity for real-time updates

### Debug Mode
Enable debug logging by setting environment variables:
```bash
export OPENAI_LOG=debug
export PYTHONPATH="${PYTHONPATH}:/path/to/project"
```

---

**Note**: This directory contains the core functionality for OpenAI Assistant integration. For application-specific code, see the `openfarma/` directory in the project root.
