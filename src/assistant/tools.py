import os
import json
import magic  # For MIME type detection
import chardet  # For character encoding detection
import openai
import streamlit as st

class FunctionCalling:
    """
    Class to manage the creation and definition of Function Calling in OpenAI.

    Provides methods to define functions, add parameters, validate their definition
    and send them to the specified assistant.
    """

    def __init__(self, api_key: str):
        """
        Initializes the class with the OpenAI API Key.

        :param api_key: The OpenAI API key.
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
        Clears the current function definition data.
        """
        self.function_data = {}

    def createFunction(self, assistant_id: str):
        """
        Creates the function in the specified assistant.

        Args:
            assistant_id (str): OpenAI assistant ID.

        Returns:
            API response when creating the function.

        Raises:
            Exception: If an error occurs during creation.
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
        Configures the basic function metadata.

        Args:
            name (str): Unique function name.
            description (str): Function description.

        Example:
            >>> fc = FunctionCalling("your-api-key")
            >>> fc.setFunctionMetadata(
            ...     name="get_weather",
            ...     description="Get the current weather in a given location"
            ... )
        """
        self.function_data['name'] = name
        self.function_data['description'] = description

    def validateFunctionDefinition(self):
        """
        Validates that the function definition is complete.

        Raises:
            ValueError: If any required field is not defined.
        """
        required_fields = ['name', 'description', 'parameters']
        for field in required_fields:
            if field not in self.function_data:
                raise ValueError(f"The field '{field}' is required and not defined.")
    
    @staticmethod
    def formatFunctionResponse(response: dict) -> str:
        """
        Formats the API response into a readable string.

        Args:
            response (dict): Raw API response.

        Returns:
            Formatted string.
        """
        return "\n".join([f"{key}: {value}" for key, value in response.items()])

    @staticmethod
    def isValidParameterType(param_type: str) -> bool:
        """
        Verifies if the parameter type is valid according to OpenAI specifications.

        Args:
            param_type (str): Parameter type to validate.

        Returns:
            True if the type is valid, False otherwise.
        """
        valid_types = ["string", "integer", "number", "boolean", "array", "object", "null"]
        return param_type in valid_types
    

class FileSearch:
    """
    Class to manage file search capabilities for OpenAI assistants using vector stores.
    
    Provides methods to create vector stores, upload files, manage batches, and 
    integrate with OpenAI assistants for enhanced file retrieval.
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
        Initializes the FileSearch class with the OpenAI API Key and creates a vector store.

        Args:
            api_key (str): The OpenAI API key.
            store_name (str): Name for the vector store.
        """
        self.api_key = api_key
        self.store_name = store_name
        self.client = openai.OpenAI(api_key=api_key)
        self.vector_store = self.client.beta.vector_stores.create(name=store_name)
        self.vector_store_id = self.vector_store.id

    @classmethod
    def isFileTypeSupported(cls, file_path: str) -> bool:
        """
        Checks if a file type is supported based on its extension.

        Args:
            file_path (str): Path to the file

        Returns:
            True if the file type is supported, False otherwise
        """
        extension = os.path.splitext(file_path)[1].lower()
        return extension in cls.SUPPORTED_MIME_TYPES

    @classmethod
    def getMimeType(cls, file_path: str) -> str:
        """
        Gets the MIME type for a given file.

        Args:
            file_path (str): Path to the file

        Returns:
            MIME type string

        Raises:
            ValueError: If file type is not supported
        """
        extension = os.path.splitext(file_path)[1].lower()
        
        if not cls.isFileTypeSupported(file_path):
            raise ValueError(f"Unsupported file type: {extension}")
            
        mime_type = cls.SUPPORTED_MIME_TYPES[extension]
        return mime_type[0] if isinstance(mime_type, list) else mime_type

    def validateFiles(self, file_paths: list) -> None:
        """
        Validates a list of files for supported types and encodings.

        Args:
            file_paths (list): List of file paths to validate

        Raises:
            ValueError: If any file is not supported or has invalid encoding
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
        Uploads multiple files to the vector store and polls for completion.

        Args:
            file_paths (list): List of paths to files to upload

        Returns:
            File batch information including status and file counts

        Raises:
            ValueError: If any file type or encoding is not supported
            Exception: If there's an error uploading files
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
        Retrieves the current status of the vector store.

        Returns:
            Vector store information including status and file counts

        Raises:
            Exception: If there's an error retrieving status
        
        Example:
            >>> fs = FileSearch("your-api-key", "Financial Reports")
            >>> status = fs.getVectorStoreStatus()
            >>> print(f"Total files: {status.file_counts.total}")
        """
        try:
            return self.client.beta.vector_stores.retrieve(vector_store_id=self.vector_store_id)
        except Exception as e:
            raise Exception(f"Error retrieving vector store status: {str(e)}")

    def listFileBatches(self) -> list:
        """
        Lists all file batches in the vector store.

        Returns:
            List of file batches

        Raises:
            Exception: If there's an error listing batches
        
        Example:
            >>> fs = FileSearch("your-api-key", "Financial Reports")
            >>> batches = fs.listFileBatches()
            >>> for batch in batches:
            ...     print(f"Batch ID: {batch.id}, Status: {batch.status}")
        """
        try:
            return self.client.beta.vector_stores.file_batches.list(
                vector_store_id=self.vector_store_id
            )
        except Exception as e:
            raise Exception(f"Error listing file batches: {str(e)}")

    def attachVectorStoreToAssistant(self, assistant_id: str) -> dict:
        """
        Attaches the vector store to an assistant for file retrieval.

        Args:
            assistant_id (str): ID of the assistant

        Returns:
            Updated assistant information

        Raises:
            Exception: If there's an error attaching the vector store
        
        Example:
            >>> fs = FileSearch("your-api-key", "Financial Reports")
            >>> response = fs.attachVectorStoreToAssistant("asst_123")
            >>> print("Vector store attached successfully")
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
        Deletes the vector store and all its contents.

        Returns:
            Response confirming deletion

        Raises:
            Exception: If there's an error deleting the vector store
        
        Example:
            >>> fs = FileSearch("your-api-key", "Financial Reports")
            >>> response = fs.deleteVectorStore()
            >>> print("Vector store deleted successfully")
        """
        try:
            return self.client.beta.vector_stores.delete(vector_store_id=self.vector_store_id)
        except Exception as e:
            raise Exception(f"Error deleting vector store: {str(e)}")