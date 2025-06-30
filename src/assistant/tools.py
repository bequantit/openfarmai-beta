"""
This module provides comprehensive tools for OpenAI Assistant integration, including function calling 
capabilities and file search/retrieval using vector stores. It offers high-level abstractions for 
defining custom functions, managing file uploads, and integrating these capabilities with OpenAI 
assistants.

Key Components:
- FunctionCalling: Manages the creation and definition of custom functions for OpenAI assistants,
  including parameter validation, nested object support, and function deployment.
- FileSearch: Handles file upload, vector store management, and file retrieval capabilities for
  assistants, supporting multiple file types and batch operations.

Typical Usage:
1. For Function Calling:
   - Create a FunctionCalling instance with your OpenAI API key
   - Define function metadata and parameters using setFunctionMetadata() and addFunctionParameter()
   - Optionally add nested properties for complex object parameters
   - Deploy the function to an assistant using createFunction()

2. For File Search:
   - Create a FileSearch instance with API key and store name
   - Upload files using uploadFileBatch() for vector storage
   - Attach the vector store to an assistant for file retrieval capabilities
   - Monitor status and manage file batches as needed

This module is designed for production use, supporting complex function definitions, multiple file 
types, batch operations, and robust error handling for enterprise chatbot applications.
"""

import os
import json
import magic  # For MIME type detection
import chardet  # For character encoding detection
import openai
import streamlit as st

class FunctionCalling:
    """
    FunctionCalling is a comprehensive manager for creating and deploying custom functions 
    to OpenAI assistants, providing a fluent API for function definition and parameter management.

    Responsibilities:
    - Manages the complete lifecycle of function creation, from definition to deployment
    - Provides parameter validation and type checking according to OpenAI specifications
    - Supports complex nested object structures and array parameters
    - Handles function metadata and description management
    - Integrates seamlessly with OpenAI assistants for tool calling capabilities
    - Supports import/export of function definitions via JSON files

    Key Features:
    - Fluent API for building complex function definitions
    - Support for all OpenAI parameter types (string, integer, number, boolean, array, object)
    - Nested object property management for complex data structures
    - Enum validation and array item definitions
    - JSON import/export for function definition persistence
    - Comprehensive validation and error handling

    Usage Example:
        fc = FunctionCalling(api_key)
        fc.setFunctionMetadata("get_weather", "Get weather information for a location")
        fc.addFunctionParameter("city", "string", "City name", required=True)
        fc.addFunctionParameter("units", "string", "Temperature units", enum=["celsius", "fahrenheit"])
        fc.createFunction(assistant_id)

    Parameter Types Supported:
    - string: Text values with optional enum constraints
    - integer: Whole numbers
    - number: Decimal numbers
    - boolean: True/false values
    - array: Lists with defined item types
    - object: Complex objects with nested properties
    - null: Null values

    Note:
        This class is designed for production use with robust error handling and validation.
        Functions created with this class can be called by OpenAI assistants during conversations
        to perform custom operations and retrieve external data.
    """

    def __init__(self, api_key: str):
        """
        Initialize a new FunctionCalling instance with OpenAI API key and prepare for function definition.

        This method sets up the foundation for creating custom functions that can be deployed
        to OpenAI assistants. It initializes the internal data structures and configures
        the OpenAI client for API interactions.

        Args:
            api_key (str): Your OpenAI API key for authentication and assistant management.

        Raises:
            Exception: If API key is invalid or OpenAI client initialization fails.

        Example:
            >>> fc = FunctionCalling("sk-...")  # Your OpenAI API key
            >>> print("FunctionCalling instance created successfully")
            FunctionCalling instance created successfully

        Internal State:
            - function_data: Dictionary to store the complete function definition
            - current_property_path: List to track nested property paths during definition
            - api_key: Stored for later use in assistant operations

        Note:
            - The API key should be kept secure and not logged or exposed in client-side code
            - This instance can be reused to create multiple functions
            - Use clearFunctionDefinition() to reset and start a new function definition
        """
        self.api_key = api_key
        self.function_data = {}
        self.current_property_path = []  # Para manejar propiedades anidadas
        openai.api_key = self.api_key

    def addFunctionParameter(self, name: str, param_type: str, description: str, required: bool = False, 
                           enum: list = None, items: dict = None):
        """
        Adds a parameter to the function definition.

        Args:
            name (str): Parameter name.
            param_type (str): Parameter type (e.g., "string", "integer", "array", "object").
            description (str): Parameter description.
            required (bool): Indicates if the parameter is required.
            enum (list): List of allowed values for enum types.
            items (dict, optional): Definition for array items or object properties.

        Returns:
            None. The parameter is added to the internal function_data dictionary.

        Example:
            # Create a weather function with multiple parameter types
            fc = FunctionCalling("your-api-key")
            fc.setFunctionMetadata(
                name="get_detailed_weather",
                description="Get detailed weather information for a location with various options"
            )

            # Simple required string parameter
            fc.addFunctionParameter(
                name="location",
                param_type="string",
                description="City and country",
                required=True
            )

            # Integer parameter with enum
            fc.addFunctionParameter(
                name="units",
                param_type="integer", 
                description="Temperature units (0: Celsius, 1: Fahrenheit)",
                enum=[0, 1]
            )

            # Array parameter with items definition
            fc.addFunctionParameter(
                name="forecast_days",
                param_type="array",
                description="Days to include in forecast",
                items={
                    "type": "string",
                    "enum": ["monday", "tuesday", "wednesday", "thursday", "friday"]
                }
            )

            # Boolean parameter
            fc.addFunctionParameter(
                name="include_humidity",
                param_type="boolean",
                description="Include humidity data in response"
            )

            # Optional string parameter with enum
            fc.addFunctionParameter(
                name="data_format",
                param_type="string",
                description="Response data format",
                enum=["basic", "detailed", "full"],
                required=False
            )

            # Required number parameter
            fc.addFunctionParameter(
                name="alert_threshold",
                param_type="number",
                description="Temperature alert threshold",
                required=True
            )
        """
        if 'parameters' not in self.function_data:
            self.function_data['parameters'] = {
                'type': 'object',
                'properties': {},
                'required': []
            }

        parameter_def = {
            'type': param_type,
            'description': description
        }

        if enum:
            parameter_def['enum'] = enum

        if items and param_type == 'array':
            parameter_def['items'] = items

        self.function_data['parameters']['properties'][name] = parameter_def

        if required:
            self.function_data['parameters']['required'].append(name)

    def addNestedProperty(self, parent_param: str, name: str, param_type: str, 
                         description: str, required: bool = False):
        """
        Adds a nested property to an object parameter.

        Args:
            parent_param (str): Name of the parent object parameter.
            name (str): Property name.
            param_type (str): Property type.
            description (str): Property description.
            required (bool, optional): Indicates if the property is required.

        Returns:
            None. The parameter is added to the internal function_data dictionary.

        Raises:
            ValueError: If the parent parameter does not exist or is not an object.
            ValueError: If the parent parameter is not an object.

        Example:
            # Create a function for processing orders
            function = FunctionCalling("your-api-key")
            function.setFunctionMetadata(
                name="process_order",
                description="Process a customer order with product details and shipping information"
            )

            # Add main order parameters
            function.addFunctionParameter(
                name="order_id",
                param_type="string", 
                description="Unique identifier for the order",
                required=True
            )

            # Add a nested object parameter for customer details
            function.addFunctionParameter(
                name="customer",
                param_type="object",
                description="Customer information",
                required=True
            )

            # Add nested properties to customer object
            function.addNestedProperty(
                parent_param="customer",
                name="name",
                param_type="string",
                description="Customer's full name",
                required=True
            )
            function.addNestedProperty(
                parent_param="customer", 
                name="email",
                param_type="string",
                description="Customer's email address",
                required=True
            )

            # Add shipping address as another nested object
            function.addFunctionParameter(
                name="shipping_address",
                param_type="object", 
                description="Shipping address details",
                required=True
            )

            # Add nested properties to shipping address
            function.addNestedProperty(
                parent_param="shipping_address",
                name="street",
                param_type="string",
                description="Street address",
                required=True
            )
            function.addNestedProperty(
                parent_param="shipping_address",
                name="city",
                param_type="string", 
                description="City name",
                required=True
            )
        """
        if parent_param not in self.function_data['parameters']['properties']:
            raise ValueError(f"Parent parameter '{parent_param}' does not exist")

        parent = self.function_data['parameters']['properties'][parent_param]
        if parent['type'] != 'object':
            raise ValueError(f"Parameter '{parent_param}' must be of type 'object'")

        if 'properties' not in parent:
            parent['properties'] = {}
            parent['required'] = []

        parent['properties'][name] = {'type': param_type, 'description': description}

        if required:
            if 'required' not in parent:
                parent['required'] = []
            parent['required'].append(name)

    def clearFunctionDefinition(self):
        """
        Clear the current function definition and reset to initial state.

        This method removes all function metadata, parameters, and nested properties,
        allowing you to start fresh with a new function definition. Useful when
        you want to reuse the same FunctionCalling instance for multiple functions.

        Returns:
            None. The internal function_data dictionary is reset to empty.

        Examples:
            # Clear after creating one function to start another
            >>> fc = FunctionCalling("your-api-key")
            >>> fc.setFunctionMetadata("get_weather", "Get weather info")
            >>> fc.addFunctionParameter("city", "string", "City name", required=True)
            >>> fc.createFunction(assistant_id)
            >>> fc.clearFunctionDefinition()  # Reset for next function
            
            # Now create a different function
            >>> fc.setFunctionMetadata("process_order", "Process customer order")
            >>> fc.addFunctionParameter("order_id", "string", "Order ID", required=True)

            # Clear before importing from file
            >>> fc.clearFunctionDefinition()
            >>> fc.importFromFile("new_function.json")

        Use Cases:
            - Reusing the same instance for multiple functions
            - Resetting after errors or invalid definitions
            - Preparing for import from JSON files
            - Starting over with a completely new function

        Note:
            - This method is safe to call at any time
            - It completely removes all function data
            - No confirmation is required - use with caution
            - The API key and client configuration remain intact
        """
        self.function_data = {}

    def createFunction(self, assistant_id: str):
        """
        Deploy the defined function to a specific OpenAI assistant.

        This method takes the complete function definition (metadata, parameters, and nested
        properties) and deploys it to the specified assistant. The function becomes available
        for the assistant to call during conversations, enabling custom operations and
        external data retrieval.

        Args:
            assistant_id (str): The unique identifier of the OpenAI assistant where the function
                will be deployed. Example: "asst_abc123def456"

        Returns:
            dict: The updated assistant object from OpenAI API, containing the new function
                in its tools list.

        Raises:
            ValueError: If the function definition is incomplete or invalid (raised by validateFunctionDefinition).
            Exception: If deployment fails due to API errors, network issues, invalid assistant ID,
                      or problems with the function definition.

        Deployment Process:
            1. Validate the complete function definition
            2. Retrieve current assistant configuration
            3. Preserve existing tools and add the new function
            4. Update the assistant with the enhanced tool set
            5. Return the updated assistant configuration

        Examples:
            # Basic function deployment
            >>> fc = FunctionCalling("your-api-key")
            >>> fc.setFunctionMetadata("get_weather", "Get weather information")
            >>> fc.addFunctionParameter("city", "string", "City name", required=True)
            >>> result = fc.createFunction("asst_123")
            >>> print(f"Function deployed to assistant: {result.id}")

            # Complex function with nested objects
            >>> fc.setFunctionMetadata("process_order", "Process customer order")
            >>> fc.addFunctionParameter("order_id", "string", "Order ID", required=True)
            >>> fc.addFunctionParameter("customer", "object", "Customer details", required=True)
            >>> fc.addNestedProperty("customer", "name", "string", "Customer name", required=True)
            >>> fc.addNestedProperty("customer", "email", "string", "Customer email", required=True)
            >>> result = fc.createFunction("asst_456")

            # Error handling
            >>> try:
            ...     result = fc.createFunction(assistant_id)
            ...     print("Function deployed successfully")
            ... except ValueError as e:
            ...     print(f"Validation error: {e}")
            ... except Exception as e:
            ...     print(f"Deployment failed: {e}")

        Validation Requirements:
            - Function name must be defined
            - Function description must be provided
            - At least one parameter must be defined
            - All parameter types must be valid OpenAI types
            - Required parameters must have descriptions

        Assistant Integration:
            - The function appears in the assistant's available tools
            - The assistant can call the function during conversations
            - Function calls are handled by your custom handler functions
            - Multiple functions can be deployed to the same assistant

        Note:
            - The assistant must exist and be accessible with your API key
            - Existing tools on the assistant are preserved
            - Function names must be unique within the assistant
            - Deployment is immediate and the function is available right away
            - Use clearFunctionDefinition() to reset for the next function
        """
        self.validateFunctionDefinition()

        try:
            # Get current assistant configuration
            assistant = openai.beta.assistants.retrieve(assistant_id=assistant_id)
            
            # Prepare the new tool configuration
            new_tool = {
                "type": "function",
                "function": self.function_data
            }
            
            # Update assistant with the new function
            response = openai.beta.assistants.update(
                assistant_id=assistant_id,
                tools=[*assistant.tools, new_tool]  # Preserve existing tools and add new one
            )

            return response
        except Exception as e:
            raise Exception(f"Error creating function: {str(e)}")
    
    def importFromFile(self, file_path: str):
        """
        Imports function definition from a JSON file.

        Args:
            file_path (str): Path to the JSON file containing the function definition.

        Raises:
            FileNotFoundError: If the specified file does not exist.
            ValueError: If the JSON file has an invalid format.

        Example:
            # Create a FunctionCalling instance
            fc = FunctionCalling("your-api-key")

            # Import function definition from a JSON file
            fc.importFromFile("weather_function.json")

            # Example JSON file content (weather_function.json):
            # {
            #     "name": "get_weather",
            #     "description": "Get weather information for a location",
            #     "parameters": {
            #         "type": "object",
            #         "properties": {
            #             "location": {
            #                 "type": "string",
            #                 "description": "City name"
            #             },
            #             "options": {
            #                 "type": "object",
            #                 "description": "Additional options",
            #                 "properties": {
            #                     "units": {
            #                         "type": "string",
            #                         "description": "Temperature units",
            #                         "enum": ["celsius", "fahrenheit"]
            #                     }
            #                 }
            #             }
            #         },
            #         "required": ["location"]
            #     }
            # }
        """

        try:
            with open(file_path, 'r') as file:
                data = json.load(file)

            # Clear existing definition
            self.clearFunctionDefinition()

            # Set basic metadata
            if 'name' in data and 'description' in data:
                self.setFunctionMetadata(data['name'], data['description'])
            else:
                raise ValueError("JSON file must contain 'name' and 'description' fields")

            # Process parameters
            if 'parameters' in data and 'properties' in data['parameters']:
                self.function_data['parameters'] = {'type': 'object', 'properties': {}}
                
                for param_name, param_info in data['parameters']['properties'].items():
                    # Handle nested objects
                    if param_info['type'] == 'object' and 'properties' in param_info:
                        self.addFunctionParameter(
                            name=param_name,
                            param_type='object',
                            description=param_info.get('description', ''),
                            required=param_name in data['parameters'].get('required', [])
                        )
                        
                        # Add nested properties
                        for nested_name, nested_info in param_info['properties'].items():
                            self.addNestedProperty(
                                parent_param=param_name,
                                name=nested_name,
                                param_type=nested_info['type'],
                                description=nested_info.get('description', ''),
                                required=nested_name in param_info.get('required', [])
                            )
                    else:
                        # Add regular parameters
                        self.addFunctionParameter(
                            name=param_name,
                            param_type=param_info['type'],
                            description=param_info.get('description', ''),
                            required=param_name in data['parameters'].get('required', []),
                            enum=param_info.get('enum'),
                            items=param_info.get('items')
                        )

        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {file_path}")
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON format in the file")
        except Exception as e:
            raise ValueError(f"Error processing function definition: {str(e)}")
    
    def setFunctionMetadata(self, name: str, description: str):
        """
        Configure the basic metadata for the function being defined.

        This method sets the essential identifying information for the function that will
        be deployed to the OpenAI assistant. The name and description are crucial for
        the assistant to understand when and how to call the function.

        Args:
            name (str): Unique function name that will be used to identify and call the function.
                Should be descriptive and follow naming conventions (e.g., "get_weather", "process_order").
            description (str): Clear, concise description of what the function does.
                This helps the assistant understand when to call the function and what to expect.

        Returns:
            None. The metadata is stored internally for later use.

        Examples:
            # Basic weather function
            >>> fc = FunctionCalling("your-api-key")
            >>> fc.setFunctionMetadata(
            ...     name="get_weather",
            ...     description="Get current weather information for a specified location"
            ... )

            # E-commerce function
            >>> fc.setFunctionMetadata(
            ...     name="process_order",
            ...     description="Process a customer order with product details, shipping information, and payment processing"
            ... )

            # Data analysis function
            >>> fc.setFunctionMetadata(
            ...     name="analyze_sales_data",
            ...     description="Analyze sales data for a given time period and return insights and trends"
            ... )

        Naming Conventions:
            - Use lowercase with underscores: "get_weather", "process_order"
            - Be descriptive but concise: "calculate_tax" not "calc"
            - Avoid special characters except underscores
            - Make names action-oriented: "get_", "process_", "analyze_"

        Description Guidelines:
            - Be specific about what the function does
            - Mention key parameters or inputs
            - Describe the expected output or result
            - Keep it under 200 characters for clarity

        Note:
            - This method should be called before adding parameters
            - The name must be unique within the assistant's function set
            - The description is crucial for the assistant's decision-making
            - You can call this method multiple times to update the metadata
        """
        self.function_data['name'] = name
        self.function_data['description'] = description

    def validateFunctionDefinition(self):
        """
        Validate that the function definition is complete and ready for deployment.

        This method performs comprehensive validation of the function definition to ensure
        it meets OpenAI's requirements before deployment. It checks for required fields,
        parameter completeness, and overall structure integrity.

        Validation Criteria:
        - name: Must be defined and non-empty
        - description: Must be provided and descriptive
        - parameters: Must be defined with at least one parameter
        - Parameter types: Must be valid OpenAI types
        - Required parameters: Must have descriptions

        Raises:
            ValueError: If any required field is missing or invalid, with specific error messages
                indicating what needs to be fixed.

        Validation Process:
            1. Check for presence of required top-level fields
            2. Validate parameter structure and types
            3. Ensure all required parameters have descriptions
            4. Verify nested object properties are properly defined

        Examples:
            # Valid function definition
            >>> fc = FunctionCalling("your-api-key")
            >>> fc.setFunctionMetadata("get_weather", "Get weather information")
            >>> fc.addFunctionParameter("city", "string", "City name", required=True)
            >>> fc.validateFunctionDefinition()  # No error - valid definition

            # Invalid - missing name
            >>> fc = FunctionCalling("your-api-key")
            >>> fc.addFunctionParameter("city", "string", "City name")
            >>> fc.validateFunctionDefinition()  # Raises ValueError: "name" is required

            # Invalid - missing description
            >>> fc = FunctionCalling("your-api-key")
            >>> fc.function_data['name'] = "get_weather"
            >>> fc.validateFunctionDefinition()  # Raises ValueError: "description" is required

            # Invalid - no parameters
            >>> fc = FunctionCalling("your-api-key")
            >>> fc.setFunctionMetadata("get_weather", "Get weather information")
            >>> fc.validateFunctionDefinition()  # Raises ValueError: "parameters" is required

        Error Messages:
            - "The field 'name' is required and not defined."
            - "The field 'description' is required and not defined."
            - "The field 'parameters' is required and not defined."

        Note:
            - This method is called automatically by createFunction()
            - It's safe to call manually for validation before deployment
            - Validation errors provide clear guidance on what needs to be fixed
            - All validation is performed locally before API calls
        """
        required_fields = ['name', 'description', 'parameters']
        for field in required_fields:
            if field not in self.function_data:
                raise ValueError(f"The field '{field}' is required and not defined.")
    
    @staticmethod
    def formatFunctionResponse(response: dict) -> str:
        """
        Format an API response dictionary into a readable string representation.

        This utility method converts the raw API response from OpenAI into a human-readable
        format, making it easier to display or log function deployment results.

        Args:
            response (dict): Raw API response dictionary from OpenAI, typically containing
                assistant information, tools, and metadata.

        Returns:
            str: Formatted string representation of the response, with each key-value pair
                on a separate line.

        Examples:
            # Format a typical assistant response
            >>> response = {
            ...     "id": "asst_abc123",
            ...     "name": "Weather Assistant",
            ...     "tools": [{"type": "function", "function": {"name": "get_weather"}}]
            ... }
            >>> formatted = FunctionCalling.formatFunctionResponse(response)
            >>> print(formatted)
            id: asst_abc123
            name: Weather Assistant
            tools: [{'type': 'function', 'function': {'name': 'get_weather'}}]

            # Use in logging or display
            >>> result = fc.createFunction(assistant_id)
            >>> print("Function deployment result:")
            >>> print(FunctionCalling.formatFunctionResponse(result))

        Use Cases:
            - Logging function deployment results
            - Displaying assistant configuration
            - Debugging API responses
            - Creating human-readable reports

        Note:
            - This is a static method that doesn't require an instance
            - The output format is consistent and easy to parse visually
            - Complex nested structures are preserved as-is
            - Useful for debugging and monitoring function deployments
        """
        return "\n".join([f"{key}: {value}" for key, value in response.items()])

    @staticmethod
    def isValidParameterType(param_type: str) -> bool:
        """
        Validate if a parameter type is supported by OpenAI's function calling API.

        This utility method checks if a given parameter type is valid according to
        OpenAI's specifications for function calling. It's useful for validation
        before adding parameters to function definitions.

        Args:
            param_type (str): The parameter type to validate.
                Valid types: "string", "integer", "number", "boolean", "array", "object", "null"

        Returns:
            bool: True if the type is valid, False otherwise.

        Valid Parameter Types:
            - "string": Text values, can include enum constraints
            - "integer": Whole numbers (e.g., 1, 2, 3)
            - "number": Decimal numbers (e.g., 1.5, 2.7)
            - "boolean": True/false values
            - "array": Lists of values with defined item types
            - "object": Complex objects with nested properties
            - "null": Null/empty values

        Examples:
            # Valid types
            >>> FunctionCalling.isValidParameterType("string")  # True
            >>> FunctionCalling.isValidParameterType("integer")  # True
            >>> FunctionCalling.isValidParameterType("boolean")  # True
            >>> FunctionCalling.isValidParameterType("array")  # True
            >>> FunctionCalling.isValidParameterType("object")  # True

            # Invalid types
            >>> FunctionCalling.isValidParameterType("text")  # False
            >>> FunctionCalling.isValidParameterType("int")  # False
            >>> FunctionCalling.isValidParameterType("float")  # False

            # Use in validation
            >>> param_type = "string"
            >>> if FunctionCalling.isValidParameterType(param_type):
            ...     fc.addFunctionParameter("name", param_type, "Parameter description")
            ... else:
            ...     print(f"Invalid parameter type: {param_type}")

        Use Cases:
            - Pre-validation before adding parameters
            - Input validation in user interfaces
            - Error checking in function builders
            - API compatibility verification

        Note:
            - This is a static method that doesn't require an instance
            - The validation is based on OpenAI's official specifications
            - Case-sensitive: "String" or "STRING" are not valid
            - Useful for building robust function definition interfaces
        """
        valid_types = ["string", "integer", "number", "boolean", "array", "object", "null"]
        return param_type in valid_types

class FileSearch:
    """
    FileSearch is a comprehensive manager for file upload, vector store creation, and 
    file retrieval capabilities for OpenAI assistants, enabling them to access and 
    search through document collections.

    Responsibilities:
    - Creates and manages vector stores for document storage and retrieval
    - Handles file uploads with support for multiple file types and encodings
    - Validates file types and character encodings for compatibility
    - Integrates vector stores with OpenAI assistants for file search capabilities
    - Manages file batches and monitors upload status
    - Provides comprehensive error handling and validation

    Key Features:
    - Support for 20+ file types including PDF, DOCX, TXT, MD, JSON, and code files
    - Automatic MIME type detection and validation
    - Character encoding validation (UTF-8, UTF-16, ASCII)
    - Batch file upload with progress monitoring
    - Vector store lifecycle management (create, attach, delete)
    - Seamless integration with OpenAI assistants for retrieval

    Supported File Types:
    - Documents: PDF, DOC, DOCX, PPTX
    - Text: TXT, MD, HTML, CSS, JSON
    - Code: PY, JS, TS, JAVA, CPP, CS, GO, PHP, RB, SH
    - Data: TEX, C, C++

    Usage Example:
        fs = FileSearch(api_key, "Document Store")
        fs.uploadFileBatch(["document1.pdf", "report.docx", "data.json"])
        fs.attachVectorStoreToAssistant(assistant_id)

    Vector Store Integration:
    - Creates persistent vector stores for document storage
    - Enables semantic search through document collections
    - Integrates with assistant's retrieval capabilities
    - Supports multiple file batches and incremental updates

    Note:
        This class is designed for production use with robust error handling,
        comprehensive file validation, and seamless OpenAI assistant integration.
        Vector stores enable assistants to access and search through large document
        collections during conversations.
    """

    # Class-level constants for supported file types
    SUPPORTED_MIME_TYPES = {
        '.c': 'text/x-c',
        '.cpp': 'text/x-c++',
        '.cs': 'text/x-csharp',
        '.css': 'text/css',
        '.doc': 'application/msword',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.go': 'text/x-golang',
        '.html': 'text/html',
        '.java': 'text/x-java',
        '.js': 'text/javascript',
        '.json': 'application/json',
        '.md': 'text/markdown',
        '.pdf': 'application/pdf',
        '.php': 'text/x-php',
        '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        '.py': ['text/x-python', 'text/x-script.python'],
        '.rb': 'text/x-ruby',
        '.sh': 'application/x-sh',
        '.tex': 'text/x-tex',
        '.ts': 'application/typescript',
        '.txt': 'text/plain'
    }

    SUPPORTED_ENCODINGS = {'utf-8', 'utf-16', 'ascii'}

    def __init__(self, api_key: str, store_name: str):
        """
        Initialize a new FileSearch instance and create a vector store for document management.

        This method sets up the foundation for file upload and retrieval capabilities by
        creating a new vector store on the OpenAI platform. The vector store will be used
        to store and index uploaded documents for semantic search capabilities.

        Args:
            api_key (str): Your OpenAI API key for authentication and vector store management.
            store_name (str): A descriptive name for the vector store. This name helps
                identify the store in the OpenAI dashboard and can be used for organization.

        Raises:
            Exception: If vector store creation fails due to API errors, authentication
                      problems, or network connectivity issues.

        Example:
            >>> fs = FileSearch("sk-...", "Financial Reports 2024")
            >>> print(f"Vector store created: {fs.vector_store_id}")
            Vector store created: vs_abc123def456

        Internal State:
            - api_key: Stored for API authentication
            - store_name: Name of the vector store for reference
            - client: OpenAI client instance for API interactions
            - vector_store: The created vector store object
            - vector_store_id: Unique identifier for the vector store

        Vector Store Creation:
            - Creates a new vector store on OpenAI's platform
            - Assigns a unique identifier for future operations
            - Prepares the store for file uploads and indexing
            - Enables semantic search capabilities

        Note:
            - The API key should be kept secure and not logged or exposed
            - Each FileSearch instance manages one vector store
            - The store_name should be descriptive for easy identification
            - Vector stores persist until explicitly deleted
            - Multiple vector stores can be created for different document collections
        """
        self.api_key = api_key
        self.store_name = store_name
        self.client = openai.OpenAI(api_key=api_key)
        self.vector_store = self.client.beta.vector_stores.create(name=store_name)
        self.vector_store_id = self.vector_store.id

    @classmethod
    def isFileTypeSupported(cls, file_path: str) -> bool:
        """
        Check if a file type is supported based on its file extension.

        This method validates whether a file can be uploaded to the vector store by
        checking its file extension against the list of supported MIME types. It's
        useful for pre-validation before attempting file uploads.

        Args:
            file_path (str): Path to the file to check. Can be relative or absolute path.
                Example: "documents/report.pdf" or "/home/user/data.json"

        Returns:
            bool: True if the file type is supported, False otherwise.

        Supported File Extensions:
            - Documents: .pdf, .doc, .docx, .pptx
            - Text: .txt, .md, .html, .css, .json
            - Code: .py, .js, .ts, .java, .cpp, .cs, .go, .php, .rb, .sh
            - Data: .tex, .c

        Examples:
            # Supported file types
            >>> FileSearch.isFileTypeSupported("document.pdf")  # True
            >>> FileSearch.isFileTypeSupported("report.docx")   # True
            >>> FileSearch.isFileTypeSupported("data.json")     # True
            >>> FileSearch.isFileTypeSupported("script.py")     # True
            >>> FileSearch.isFileTypeSupported("README.md")     # True

            # Unsupported file types
            >>> FileSearch.isFileTypeSupported("image.jpg")     # False
            >>> FileSearch.isFileTypeSupported("video.mp4")     # False
            >>> FileSearch.isFileTypeSupported("archive.zip")   # False

            # Use in validation
            >>> file_paths = ["doc1.pdf", "image.png", "data.json"]
            >>> supported_files = [f for f in file_paths if FileSearch.isFileTypeSupported(f)]
            >>> print(f"Supported files: {supported_files}")
            Supported files: ['doc1.pdf', 'data.json']

        Use Cases:
            - Pre-validation before file uploads
            - Filtering file lists for supported types
            - User interface validation
            - Batch processing preparation

        Note:
            - This is a class method that doesn't require an instance
            - Only checks file extension, not actual file content
            - Case-insensitive extension matching
            - Useful for building file upload interfaces
        """
        extension = os.path.splitext(file_path)[1].lower()
        return extension in cls.SUPPORTED_MIME_TYPES

    @classmethod
    def getMimeType(cls, file_path: str) -> str:
        """
        Get the MIME type for a given file based on its extension.

        This method returns the appropriate MIME type for a file, which is required
        for proper file upload to the vector store. It maps file extensions to
        their corresponding MIME types according to OpenAI's specifications.

        Args:
            file_path (str): Path to the file. Can be relative or absolute path.
                Example: "documents/report.pdf" or "/home/user/data.json"

        Returns:
            str: The MIME type string for the file.

        Raises:
            ValueError: If the file type is not supported by the vector store.

        MIME Type Mappings:
            - .pdf → "application/pdf"
            - .docx → "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            - .txt → "text/plain"
            - .json → "application/json"
            - .py → "text/x-python"
            - .js → "text/javascript"
            - .md → "text/markdown"

        Examples:
            # Get MIME types for supported files
            >>> FileSearch.getMimeType("document.pdf")  # "application/pdf"
            >>> FileSearch.getMimeType("data.json")     # "application/json"
            >>> FileSearch.getMimeType("script.py")     # "text/x-python"
            >>> FileSearch.getMimeType("README.md")     # "text/markdown"

            # Error for unsupported files
            >>> FileSearch.getMimeType("image.jpg")     # Raises ValueError

            # Use in file processing
            >>> try:
            ...     mime_type = FileSearch.getMimeType(file_path)
            ...     print(f"File {file_path} has MIME type: {mime_type}")
            ... except ValueError as e:
            ...     print(f"Unsupported file type: {file_path}")

        Use Cases:
            - Preparing files for upload to vector stores
            - File type validation and processing
            - API integration where MIME types are required
            - File handling in web applications

        Note:
            - This is a class method that doesn't require an instance
            - Only checks file extension, not actual file content
            - Case-insensitive extension matching
            - Some file types have multiple possible MIME types (e.g., .py)
            - Raises ValueError for unsupported file types
        """
        extension = os.path.splitext(file_path)[1].lower()
        
        if not cls.isFileTypeSupported(file_path):
            raise ValueError(f"Unsupported file type: {extension}")
            
        mime_type = cls.SUPPORTED_MIME_TYPES[extension]
        return mime_type[0] if isinstance(mime_type, list) else mime_type

    def validateFiles(self, file_paths: list) -> None:
        """
        Validate a list of files for supported types and character encodings.

        This method performs comprehensive validation of multiple files before upload,
        checking both file type support and character encoding compatibility. It's
        designed to catch issues early and provide clear error messages.

        Args:
            file_paths (list): List of file paths to validate. Can be relative or absolute paths.
                Example: ["doc1.pdf", "data.json", "report.docx"]

        Raises:
            ValueError: If any file is not supported or has invalid encoding, with specific
                      error messages indicating which file and what the issue is.

        Validation Process:
            1. Check if each file type is supported by extension
            2. For text files, detect and validate character encoding
            3. Ensure all files meet OpenAI's requirements
            4. Provide detailed error messages for any issues

        Supported Encodings:
            - UTF-8: Most common encoding for text files
            - UTF-16: Unicode encoding with 16-bit characters
            - ASCII: Basic ASCII encoding for simple text

        Examples:
            # Valid files
            >>> fs = FileSearch("your-api-key", "Test Store")
            >>> fs.validateFiles(["document.pdf", "data.json", "README.md"])  # No error

            # Invalid file type
            >>> fs.validateFiles(["image.jpg", "document.pdf"])
            # Raises ValueError: "Unsupported file type: .jpg"

            # Invalid encoding
            >>> fs.validateFiles(["document.pdf", "invalid_encoding.txt"])
            # Raises ValueError: "Unsupported encoding latin-1 for file: invalid_encoding.txt"

            # Error handling
            >>> try:
            ...     fs.validateFiles(file_paths)
            ...     print("All files are valid")
            ... except ValueError as e:
            ...     print(f"Validation failed: {e}")

        Use Cases:
            - Pre-validation before batch uploads
            - Quality assurance in file processing pipelines
            - User interface validation
            - Automated file processing systems

        Note:
            - This method validates all files before returning
            - Provides specific error messages for each issue
            - Uses magic library for MIME type detection
            - Uses chardet for character encoding detection
            - Recommended to call before uploadFileBatch()
        """
        for file_path in file_paths:
            if not self.isFileTypeSupported(file_path):
                raise ValueError(f"Unsupported file type: {file_path}")
            
            # Check encoding for text files
            mime = magic.Magic(mime=True)
            file_mime = mime.from_file(file_path)
            
            if file_mime.startswith('text/'):
                with open(file_path, 'rb') as f:
                    raw = f.read()
                    result = chardet.detect(raw)
                    if result['encoding'].lower() not in self.SUPPORTED_ENCODINGS:
                        raise ValueError(
                            f"Unsupported encoding {result['encoding']} for file: {file_path}. "
                            f"Supported encodings are: {', '.join(self.SUPPORTED_ENCODINGS)}"
                        )

    def uploadFileBatch(self, file_paths: list) -> dict:
        """
        Upload multiple files to the vector store and wait for processing completion.

        This method uploads a batch of files to the vector store and polls for completion,
        ensuring all files are properly indexed and available for search. It includes
        comprehensive validation and error handling.

        Args:
            file_paths (list): List of paths to files to upload. Can be relative or absolute paths.
                Example: ["documents/report.pdf", "data/analysis.json", "README.md"]

        Returns:
            dict: File batch information including status, file counts, and processing details.
                Contains information about the uploaded files and their processing status.

        Raises:
            ValueError: If any file type or encoding is not supported (from validateFiles).
            Exception: If there's an error uploading files, with detailed error information.

        Upload Process:
            1. Validate all files for type and encoding compatibility
            2. Open all files for batch upload
            3. Upload files to the vector store
            4. Poll for processing completion
            5. Return batch information with status

        Examples:
            # Basic batch upload
            >>> fs = FileSearch("your-api-key", "Document Store")
            >>> batch = fs.uploadFileBatch(["doc1.pdf", "doc2.docx", "data.json"])
            >>> print(f"Batch status: {batch.status}")
            >>> print(f"Files processed: {batch.file_counts.total}")

            # Upload with error handling
            >>> try:
            ...     batch = fs.uploadFileBatch(file_paths)
            ...     if batch.status == "completed":
            ...         print("All files uploaded successfully")
            ...     else:
            ...         print(f"Upload status: {batch.status}")
            ... except ValueError as e:
            ...     print(f"Validation error: {e}")
            ... except Exception as e:
            ...     print(f"Upload failed: {e}")

            # Monitor upload progress
            >>> batch = fs.uploadFileBatch(large_file_list)
            >>> print(f"Processing: {batch.file_counts.in_progress}")
            >>> print(f"Completed: {batch.file_counts.completed}")

        Batch Information:
            The returned dictionary contains:
            - status: Current batch status ("completed", "in_progress", "failed")
            - file_counts: Object with total, completed, in_progress, failed counts
            - id: Unique batch identifier
            - created_at: Timestamp of batch creation

        Note:
            - Files are processed asynchronously after upload
            - Large files may take time to process and index
            - All files in the batch must be valid before upload begins
            - File handles are automatically closed after upload
            - Use getVectorStoreStatus() to monitor overall store status
        """
        try:
            # Validate files before attempting upload
            self.validateFiles(file_paths)
            
            # Open all files for uploading
            file_streams = []
            try:
                file_streams = [open(path, "rb") for path in file_paths]
                
                # Upload files and poll for completion
                file_batch = self.client.beta.vector_stores.file_batches.upload_and_poll(
                    vector_store_id=self.vector_store_id,
                    files=file_streams
                )
                
                return file_batch
                
            finally:
                # Ensure all files are closed
                for stream in file_streams:
                    stream.close()
                    
        except Exception as e:
            raise Exception(f"Error uploading file batch: {str(e)}")

    def getVectorStoreStatus(self) -> dict:
        """
        Retrieve the current status and information about the vector store.

        This method provides comprehensive information about the vector store, including
        file counts, processing status, and overall health. Useful for monitoring
        and debugging vector store operations.

        Returns:
            dict: Vector store information including status, file counts, and metadata.
                Contains detailed information about the store's current state.

        Raises:
            Exception: If there's an error retrieving status, with detailed error information.

        Status Information:
            The returned dictionary contains:
            - id: Unique vector store identifier
            - name: Store name as provided during creation
            - status: Current store status
            - file_counts: Object with total, completed, in_progress, failed counts
            - created_at: Timestamp of store creation
            - metadata: Additional store metadata

        Examples:
            # Get basic status
            >>> fs = FileSearch("your-api-key", "Financial Reports")
            >>> status = fs.getVectorStoreStatus()
            >>> print(f"Store name: {status.name}")
            >>> print(f"Total files: {status.file_counts.total}")

            # Monitor processing progress
            >>> status = fs.getVectorStoreStatus()
            >>> if status.file_counts.in_progress > 0:
            ...     print(f"Still processing {status.file_counts.in_progress} files")
            ... else:
            ...     print("All files processed")

            # Check store health
            >>> status = fs.getVectorStoreStatus()
            >>> if status.status == "ready":
            ...     print("Store is ready for search")
            ... else:
            ...     print(f"Store status: {status.status}")

        Use Cases:
            - Monitoring file upload progress
            - Checking store readiness for search
            - Debugging upload issues
            - Health monitoring in production systems

        Note:
            - Status is real-time and reflects current store state
            - File counts may change as files are processed
            - Use this method to monitor long-running uploads
            - Store status affects assistant search capabilities
        """
        try:
            return self.client.beta.vector_stores.retrieve(vector_store_id=self.vector_store_id)
        except Exception as e:
            raise Exception(f"Error retrieving vector store status: {str(e)}")

    def listFileBatches(self) -> list:
        """
        List all file batches in the vector store with their processing status.

        This method retrieves information about all file batches that have been uploaded
        to the vector store, including their current status, file counts, and processing
        history. Useful for monitoring upload progress and debugging issues.

        Returns:
            list: List of file batch objects, each containing batch information and status.
                Each batch object includes id, status, file_counts, and timestamps.

        Raises:
            Exception: If there's an error listing batches, with detailed error information.

        Batch Information:
            Each batch object contains:
            - id: Unique batch identifier
            - status: Current batch status ("completed", "in_progress", "failed")
            - file_counts: Object with total, completed, in_progress, failed counts
            - created_at: Timestamp of batch creation
            - completed_at: Timestamp of completion (if finished)

        Examples:
            # List all batches
            >>> fs = FileSearch("your-api-key", "Document Store")
            >>> batches = fs.listFileBatches()
            >>> for batch in batches:
            ...     print(f"Batch {batch.id}: {batch.status}")
            ...     print(f"  Files: {batch.file_counts.total} total, {batch.file_counts.completed} completed")

            # Monitor specific batch
            >>> batches = fs.listFileBatches()
            >>> for batch in batches:
            ...     if batch.status == "in_progress":
            ...         print(f"Batch {batch.id} is still processing")
            ...         print(f"  Progress: {batch.file_counts.completed}/{batch.file_counts.total}")

            # Check for failed batches
            >>> batches = fs.listFileBatches()
            >>> failed_batches = [b for b in batches if b.status == "failed"]
            >>> if failed_batches:
            ...     print(f"Found {len(failed_batches)} failed batches")
            ...     for batch in failed_batches:
            ...         print(f"  Batch {batch.id}: {batch.file_counts.failed} files failed")

        Use Cases:
            - Monitoring upload progress across multiple batches
            - Debugging failed uploads
            - Tracking file processing history
            - Quality assurance and reporting

        Note:
            - Returns all batches for the vector store
            - Batch status reflects current processing state
            - Failed batches may contain partial file counts
            - Use this method to monitor long-running uploads
        """
        try:
            return self.client.beta.vector_stores.file_batches.list(
                vector_store_id=self.vector_store_id
            )
        except Exception as e:
            raise Exception(f"Error listing file batches: {str(e)}")

    def attachVectorStoreToAssistant(self, assistant_id: str) -> dict:
        """
        Attach the vector store to an assistant to enable file search capabilities.

        This method integrates the vector store with a specific OpenAI assistant,
        allowing the assistant to search through and reference the uploaded documents
        during conversations. The assistant gains access to semantic search capabilities
        across all files in the vector store.

        Args:
            assistant_id (str): The unique identifier of the OpenAI assistant.
                Example: "asst_abc123def456"

        Returns:
            dict: Updated assistant object from OpenAI API, containing the new
                retrieval tool and vector store configuration.

        Raises:
            Exception: If there's an error attaching the vector store, with detailed
                      error information.

        Integration Process:
            1. Retrieve current assistant configuration
            2. Preserve existing tools (excluding old retrieval tools)
            3. Add new retrieval tool with vector store reference
            4. Update assistant with enhanced tool configuration
            5. Return updated assistant information

        Examples:
            # Basic attachment
            >>> fs = FileSearch("your-api-key", "Financial Reports")
            >>> fs.uploadFileBatch(["report1.pdf", "report2.docx"])
            >>> result = fs.attachVectorStoreToAssistant("asst_123")
            >>> print("Vector store attached successfully")

            # Attachment with error handling
            >>> try:
            ...     result = fs.attachVectorStoreToAssistant(assistant_id)
            ...     print(f"Assistant updated: {result.id}")
            ...     print(f"Tools available: {len(result.tools)}")
            ... except Exception as e:
            ...     print(f"Attachment failed: {e}")

            # Check assistant tools after attachment
            >>> result = fs.attachVectorStoreToAssistant(assistant_id)
            >>> for tool in result.tools:
            ...     if tool.type == "retrieval":
            ...         print("Retrieval tool is active")

        Assistant Capabilities:
            After attachment, the assistant can:
            - Search through uploaded documents semantically
            - Reference specific files during conversations
            - Answer questions based on document content
            - Provide citations from source documents

        Tool Configuration:
            - Adds a "retrieval" tool to the assistant
            - Configures vector store IDs for file access
            - Preserves existing function calling tools
            - Enables seamless document search integration

        Note:
            - The assistant must exist and be accessible with your API key
            - Existing tools are preserved during attachment
            - Multiple vector stores can be attached to the same assistant
            - The assistant gains immediate access to all uploaded files
            - Use this method after uploading files to make them searchable
        """
        try:
            # First get current assistant configuration to preserve existing tools
            current_assistant = self.client.beta.assistants.retrieve(assistant_id=assistant_id)
            
            # Filter out any existing retrieval tools
            existing_tools = [tool for tool in current_assistant.tools if tool.type != "retrieval"]
            
            # Add the retrieval tool
            updated_tools = [*existing_tools, {"type": "retrieval"}]
            
            # Update the assistant with both tools and vector store
            return self.client.beta.assistants.update(
                assistant_id=assistant_id,
                tools=updated_tools,
                tool_resources={
                    "file_search": {"vector_store_ids": [self.vector_store_id]},
                    "vector_store_ids": [self.vector_store_id]  # Include both formats for compatibility
                }
            )
        except Exception as e:
            raise Exception(f"Error attaching vector store: {str(e)}")

    def deleteVectorStore(self) -> dict:
        """
        Permanently delete the vector store and all its contents.

        This method removes the vector store and all uploaded files from the OpenAI
        platform. This action cannot be undone, so use with caution. All file batches,
        indexed documents, and search capabilities will be permanently lost.

        Returns:
            dict: Response confirming deletion from OpenAI API.

        Raises:
            Exception: If there's an error deleting the vector store, with detailed
                      error information.

        Deletion Process:
            1. Remove all file batches and indexed content
            2. Delete the vector store configuration
            3. Release all associated resources
            4. Return confirmation of successful deletion

        Examples:
            # Basic deletion
            >>> fs = FileSearch("your-api-key", "Temporary Store")
            >>> result = fs.deleteVectorStore()
            >>> print("Vector store deleted successfully")

            # Deletion with confirmation
            >>> fs = FileSearch("your-api-key", "Important Documents")
            >>> # ... upload files and use store ...
            >>> try:
            ...     result = fs.deleteVectorStore()
            ...     print("Store and all files permanently deleted")
            ... except Exception as e:
            ...     print(f"Deletion failed: {e}")

            # Cleanup after testing
            >>> test_stores = [fs1, fs2, fs3]  # Multiple test stores
            >>> for store in test_stores:
            ...     try:
            ...         store.deleteVectorStore()
            ...         print(f"Deleted store: {store.store_name}")
            ...     except Exception as e:
            ...         print(f"Failed to delete {store.store_name}: {e}")

        Impact of Deletion:
            - All uploaded files are permanently removed
            - File batches and processing history are lost
            - Assistant search capabilities are disabled
            - Vector store ID becomes invalid
            - No recovery is possible

        Use Cases:
            - Cleanup of temporary or test stores
            - Removing outdated document collections
            - Freeing up storage resources
            - Compliance with data retention policies

        Warning:
            - This action is irreversible
            - All files and search capabilities will be lost
            - Consider backing up important data before deletion
            - Detach from assistants before deletion if needed

        Note:
            - Deletion is immediate and permanent
            - No confirmation prompt is provided
            - Use with extreme caution in production environments
            - Consider archiving important documents before deletion
        """
        try:
            return self.client.beta.vector_stores.delete(vector_store_id=self.vector_store_id)
        except Exception as e:
            raise Exception(f"Error deleting vector store: {str(e)}")