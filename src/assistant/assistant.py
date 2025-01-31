import json, openai

class Assistant:
    """
    Class to manage OpenAI assistants creation and configuration.

    Provides methods to create assistants, set instructions, and manage their configuration
    in the OpenAI playground.

    Attributes:
        api_key: The OpenAI API key.
        client: The OpenAI client.
        assistant_data: The assistant configuration data.
    
    Methods:
        setMetadata: Sets the basic metadata for the assistant.
        setModel: Sets the model to be used by the assistant.
        addTool: Adds a tool to the assistant's capabilities.
        create: Creates the assistant in OpenAI.
        importFromFile: Imports assistant configuration from a JSON file.
        clearConfiguration: Clears the current assistant configuration.
        setTemperature: Sets the temperature for the model's responses.
        setTopP: Sets the top_p value for nucleus sampling.
        setResponseFormat: Sets the response format for the assistant.
        loadFromId: Loads an existing assistant's configuration using its ID.

    Example:
        >>> assistant = Assistant("your-api-key")
        >>> assistant.setMetadata("Math Tutor", "A helpful math tutor", instructions)
        >>> assistant.setModel("gpt-4")
        >>> assistant.addTool("code_interpreter")
        >>> assistant.create()

    Note:
        - The assistant configuration is stored in the assistant_data attribute.
        - The create method sends the assistant configuration to OpenAI and returns the response.
    """

    def __init__(self, api_key: str):
        """
        Initializes the Assistant class with the OpenAI API Key.

        Args:
            api_key (str): The OpenAI API key.
        """
        self.api_key = api_key
        self.client = openai.OpenAI(api_key=api_key)  # Initialize the client
        self.assistant_data = {
            'model': 'gpt-4-turbo-preview',
            'tools': [],
            'temperature': 0.7,  # Default temperature
            'top_p': 1.0,       # Default top_p
            'response_format': {"type": "text"}  # Default response format
        }

    def setMetadata(self, name: str, description: str, instructions: str):
        """
        Sets the basic metadata for the assistant.

        Args:
            name (str): Name of the assistant.
            description (str): Brief description of the assistant.
            instructions (str): Detailed instructions for the assistant's behavior.
        """
        self.assistant_data['name'] = name
        self.assistant_data['description'] = description
        self.assistant_data['instructions'] = instructions

    def setModel(self, model: str):
        """
        Sets the model to be used by the assistant.

        Args:
            model (str): The OpenAI model identifier (e.g., 'gpt-4-turbo-preview', 'gpt-3.5-turbo').
        """
        self.assistant_data['model'] = model

    def addTool(self, tool_type: str, function: dict = None):
        """
        Adds a tool to the assistant's capabilities.

        Args:
            tool_type (str): Type of tool ('code_interpreter', 'retrieval', or 'function').
            function (dict): Function definition if tool_type is 'function'.
        Raises:
            ValueError: If tool_type is invalid or function is missing when required.

        Example:
            >>> assistant = Assistant("your-api-key")
            
            # Add code interpreter tool
            >>> assistant.addTool("code_interpreter")
            
            # Add retrieval tool
            >>> assistant.addTool("retrieval")
            
            # Add function tool
            >>> fc = FunctionCalling("your-api-key")
            >>> fc.setFunctionMetadata(
            ...     name="get_weather",
            ...     description="Get current weather in a location"
            ... )
            >>> fc.addFunctionParameter(
            ...     name="location",
            ...     param_type="string",
            ...     description="City and country",
            ...     required=True
            ... )
            >>> assistant.addTool("function", fc.function_data)
        """
        valid_tools = ['code_interpreter', 'retrieval', 'function']
        if tool_type not in valid_tools:
            raise ValueError(f"Invalid tool type. Must be one of: {', '.join(valid_tools)}")

        if tool_type == 'function' and not function:
            raise ValueError("Function definition is required when adding a function tool")

        tool = {'type': tool_type}
        if function:
            tool['function'] = function

        self.assistant_data['tools'].append(tool)

    def create(self) -> dict:
        """
        Creates the assistant in OpenAI.

        Returns:
            The response from OpenAI API containing the assistant details.
        Raises:
            ValueError: If required fields are missing.

        Example:
            >>> assistant = Assistant("your-api-key")
            
            # Set required metadata
            >>> assistant.setMetadata(
            ...     name="Math Tutor",
            ...     description="A helpful math tutor",
            ...     instructions="You are a math tutor. Help students solve problems."
            ... )
            
            # Create the assistant
            >>> response = assistant.create()
            >>> print(f"Assistant created with ID: {response.id}")
        """
        required_fields = ['name', 'instructions']
        for field in required_fields:
            if field not in self.assistant_data:
                raise ValueError(f"Missing required field: {field}")

        try:
            response = self.client.beta.assistants.create(**self.assistant_data)
            self.assistant_id = response.id
            return response
        except Exception as e:
            raise Exception(f"Error creating assistant: {str(e)}")

    def importFromFile(self, file_path: str):
        """
        Imports assistant configuration from a JSON file.

        Args:
            file_path (str): Path to the JSON file containing the assistant configuration.
        Raises:
            FileNotFoundError: If the specified file doesn't exist.
            ValueError: If the JSON file has an invalid format.

        Example:
            >>> # Example JSON file (assistant_config.json):
            >>> # {
            >>> #     "name": "Math Tutor",
            >>> #     "description": "A helpful math tutor",
            >>> #     "instructions": "You are a math tutor. Help students solve problems.",
            >>> #     "model": "gpt-4-turbo-preview",
            >>> #     "tools": [
            >>> #         {"type": "code_interpreter"},
            >>> #         {
            >>> #             "type": "function",
            >>> #             "function": {
            >>> #                 "name": "solve_equation",
            >>> #                 "description": "Solves a mathematical equation",
            >>> #                 "parameters": {
            >>> #                     "type": "object",
            >>> #                     "properties": {
            >>> #                         "equation": {
            >>> #                             "type": "string",
            >>> #                             "description": "The equation to solve"
            >>> #                         }
            >>> #                     },
            >>> #                     "required": ["equation"]
            >>> #                 }
            >>> #             }
            >>> #         }
            >>> #     ]
            >>> # }
            >>> 
            >>> assistant = Assistant("your-api-key")
            >>> assistant.importFromFile("assistant_config.json")
            >>> response = assistant.create()
            >>> print(f"Assistant created with ID: {response.id}")
        """
        try:
            with open(file_path, 'r') as file:
                data = json.load(file)

            required_fields = ['name', 'description', 'instructions']
            if not all(field in data for field in required_fields):
                raise ValueError("JSON file must contain 'name', 'description', and 'instructions' fields")

            self.setMetadata(data['name'], data['description'], data['instructions'])

            if 'model' in data:
                self.setModel(data['model'])

            if 'tools' in data:
                for tool in data['tools']:
                    self.addTool(tool['type'], tool.get('function'))

            if 'temperature' in data:
                self.setTemperature(data['temperature'])

            if 'top_p' in data:
                self.setTopP(data['top_p'])

        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {file_path}")
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON format in the file")
        except Exception as e:
            raise ValueError(f"Error processing assistant configuration: {str(e)}")

    def clearConfiguration(self):
        """
        Clears the current assistant configuration.
        """
        self.assistant_data = {
            'model': 'gpt-4-turbo-preview',
            'tools': []
        }

    def setTemperature(self, temperature: float):
        """
        Sets the temperature for the model's responses.

        Args:
            temperature (float): Float between 0 and 2. Higher values make output more random,
                          lower values make it more deterministic.
        Raises:
            ValueError: If temperature is not between 0 and 2.
        """
        if not 0 <= temperature <= 2:
            raise ValueError("Temperature must be between 0 and 2")
        self.assistant_data['temperature'] = temperature

    def setTopP(self, top_p: float):
        """
        Sets the top_p value for nucleus sampling.

        Args:
            top_p (float): Float between 0 and 1. Lower values increase focus on more likely tokens.
        Raises:
            ValueError: If top_p is not between 0 and 1.
        """
        if not 0 <= top_p <= 1:
            raise ValueError("Top_p must be between 0 and 1")
        self.assistant_data['top_p'] = top_p

    def setResponseFormat(self, format_type: str):
        """
        Sets the response format for the assistant.

        Args:
            format_type (str): Either "text" or "json_object"
        Raises:
            ValueError: If format_type is not valid.
        
        Example:
            >>> assistant = Assistant("your-api-key")
            >>> assistant.setResponseFormat("json_object")  # For JSON responses
            >>> assistant.setResponseFormat("text")         # For text responses
        """
        valid_formats = ["text", "json_object"]
        if format_type not in valid_formats:
            raise ValueError(f"Response format must be one of: {', '.join(valid_formats)}")
        self.assistant_data['response_format'] = {"type": format_type}

    def loadFromId(self, assistant_id: str):
        """
        Loads an existing assistant's configuration using its ID.

        Args:
            assistant_id (str): The ID of the existing OpenAI assistant.
        Raises:
            Exception: If the assistant cannot be found or there's an API error.
        
        Example:
            >>> assistant = Assistant("your-api-key")
            >>> assistant.loadFromId("asst_abc123")
            >>> print(assistant.assistant_data['name'])  # Access the loaded configuration
        """
        try:
            # Retrieve the assistant from OpenAI using client
            existing_assistant = self.client.beta.assistants.retrieve(assistant_id=assistant_id)
            
            # Update assistant_data with all attributes
            self.assistant_data = {
                'name': existing_assistant.name,
                'description': existing_assistant.description,
                'instructions': existing_assistant.instructions,
                'model': existing_assistant.model,
                'tools': existing_assistant.tools,
                'temperature': getattr(existing_assistant, 'temperature', 0.7),  # Default if not set
                'top_p': getattr(existing_assistant, 'top_p', 1.0),  # Default if not set
                'response_format': getattr(existing_assistant, 'response_format', {"type": "text"})  # Default if not set
            }
            
            # Remove None values to avoid API errors
            self.assistant_data = {k: v for k, v in self.assistant_data.items() if v is not None}
            
        except Exception as e:
            raise Exception(f"Error loading assistant: {str(e)}")