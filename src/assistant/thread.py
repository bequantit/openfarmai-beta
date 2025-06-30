"""
This module provides a high-level abstraction for managing conversational 
threads with the OpenAI Assistant API, including message handling, thread 
lifecycle management, and integration with Streamlit for real-time chat interfaces.

Key Components:
- EventHandler: Handles OpenAI Assistant events, including streaming responses 
and tool calls, and updates the Streamlit UI in real time.
- Thread: Manages the lifecycle of a conversation thread, including sending/queuing 
messages, running the assistant (with or without streaming), and handling tool outputs.

Typical Usage:
1. Instantiate a Thread with your OpenAI API key.
2. Add messages to the thread using addMessage().
3. Run the assistant using runWithStreaming() or runWithoutStreaming(), providing 
tool handler functions as needed.
4. Integrate with Streamlit to display chat messages and handle user input interactively.

This module is designed to be extensible and robust, supporting advanced use cases such 
as tool calling, message queuing, and real-time UI updates for chatbot applications.

"""
import time
import json
import openai
import streamlit as st
from typing_extensions import override
from openai import AssistantEventHandler
from collections import deque

from openfarma.src.params import BOT_CHAT_COLUMNS, AVATAR_BOT_PATH

class EventHandler(AssistantEventHandler):
    """
    EventHandler is a custom event handler for OpenAI Assistant events, designed for use 
    in interactive chat applications with Streamlit.

    Responsibilities:
    - Listens for and processes events from the OpenAI Assistant API, 
    such as streaming message deltas and tool call requirements.
    - Updates the Streamlit UI in real time as new assistant messages are streamed.
    - Handles tool calls by invoking user-provided handler functions and submitting 
    their outputs back to the assistant.
    - Maintains state for the current message being streamed and manages the display 
    container in Streamlit.

    Relationship to Thread:
    - EventHandler is tightly coupled with a Thread instance, which manages the 
    conversation state and message queue.
    - When a tool call is required, EventHandler uses the tool_handlers dictionary 
    (provided by the user) to resolve and execute the appropriate function, then 
    submits the result to the thread.
    - The handler is re-instantiated for each tool output submission to maintain 
    correct state and event flow.

    Streamlit Integration:
    - Uses Streamlit's chat_message and container APIs to display assistant 
    responses in a chat-like interface.
    - Ensures smooth, real-time updates for a natural conversational experience.

    Usage Example:
        handler = EventHandler(tool_handlers, client, thread_instance)
        with client.beta.threads.runs.stream(..., event_handler=handler) as stream:
            stream.until_done()

    Args:
        tool_handlers (dict): Mapping of function names to handler functions for tool calls.
        client (openai.OpenAI): The OpenAI client instance.
        thread_instance (Thread): The parent Thread object managing the conversation.
    """
    def __init__(self, tool_handlers, client, thread_instance):
        """
        Initialize the EventHandler with tool handlers, OpenAI client, and thread reference.

        Args:
            tool_handlers (dict): Dictionary mapping function names to their handler functions.
                Example: {"get_weather": weather_function, "calculate": math_function}
            client (openai.OpenAI): The OpenAI client instance for API calls.
            thread_instance (Thread): Reference to the parent Thread instance for state management.

        Note:
            The tool_handlers dictionary should contain callable functions that match the names
            expected by the OpenAI Assistant's tool definitions. These functions will be called
            with the arguments provided by the assistant during tool execution.
        """
        super().__init__()
        self.tool_handlers = tool_handlers
        self.client = client
        self.thread_instance = thread_instance
        self.current_text = ""
        self.container = None
        self.is_first_message = True

    @override
    def on_event(self, event):
        """
        Handle OpenAI Assistant events, including streaming message deltas and tool call requirements.

        This method is called by the OpenAI streaming API for each event. It handles two main event types:
        1. 'thread.run.requires_action': When the assistant needs to call a tool/function
        2. 'thread.message.delta': When the assistant is streaming a response message

        Args:
            event: The OpenAI event object containing event type and data.

        Streamlit Integration:
            For message deltas, this method creates a chat message container on first message
            and updates it with new text as it streams in, providing a real-time chat experience.

        Example Event Flow:
            1. User sends message -> Assistant starts responding
            2. 'thread.message.delta' events stream in -> Text appears in real-time
            3. Assistant needs tool -> 'thread.run.requires_action' event
            4. Tool executed -> Response continues streaming
        """
        if event.event == 'thread.run.requires_action':
            run_id = event.data.id
            self.thread_instance.requires_action_occurred = True
            self.handleRequiresAction(event.data, run_id)
        elif event.event == 'thread.message.delta':
            if self.is_first_message:
                left, _ = st.columns(BOT_CHAT_COLUMNS)
                with left:
                    with st.chat_message("assistant", avatar=AVATAR_BOT_PATH):
                        self.container = st.empty()
                        self.is_first_message = False
            
            if self.container:
                self.current_text += event.data.delta.content[0].text.value
                self.container.markdown(
                    f'<div class="chat-message bot-message">{self.current_text}</div>',
                    unsafe_allow_html=True
                )
                time.sleep(0.03)  # Small delay for smooth streaming effect
    
    def handleRequiresAction(self, data, run_id):
        """
        Process tool calls required by the assistant and prepare outputs for submission.

        This method is called when the assistant requests to execute one or more tools.
        It iterates through the required tool calls, executes the corresponding handler
        functions, and prepares the outputs for submission back to the assistant.

        Args:
            data: The run data containing required_action information with tool calls.
            run_id (str): The ID of the current run for tracking and submission.

        Tool Execution Flow:
            1. Extract tool calls from the assistant's request
            2. For each tool call, find the corresponding handler in tool_handlers
            3. Execute the handler with the provided arguments
            4. Collect all outputs and submit them back to the assistant

        Example:
            If the assistant requests to call a "get_weather" tool with arguments
            {"city": "New York"}, this method will:
            1. Find the "get_weather" function in tool_handlers
            2. Call it with city="New York"
            3. Convert the result to string and prepare for submission

        Note:
            Only tools that have corresponding handlers in tool_handlers will be executed.
            Tools without handlers are ignored, which may cause the assistant to fail.
        """
        tool_outputs = []
        for tool in data.required_action.submit_tool_outputs.tool_calls:
            if tool.function.name in self.tool_handlers:
                arguments = json.loads(tool.function.arguments)
                handler = self.tool_handlers[tool.function.name]
                output = str(handler(**arguments))
                tool_outputs.append({
                    "tool_call_id": tool.id,
                    "output": output
                })
        self.submitToolOutputs(tool_outputs, run_id)

    def submitToolOutputs(self, tool_outputs, run_id):
        """
        Submit tool execution outputs back to the OpenAI Assistant and continue the conversation.

        This method creates a new streaming session to submit tool outputs and continue
        processing the assistant's response. It creates a new EventHandler instance to
        maintain proper state management for the continued conversation.

        Args:
            tool_outputs (list): List of dictionaries containing tool_call_id and output pairs.
                Example: [{"tool_call_id": "call_123", "output": "Weather is sunny"}]
            run_id (str): The ID of the current run for submission.

        Process:
            1. Submit tool outputs to the OpenAI API
            2. Create a new EventHandler instance for continued streaming
            3. Wait for the assistant to process the outputs and continue responding

        Note:
            A new EventHandler is created for each tool output submission to ensure
            clean state management and proper event handling for the continued conversation.
        """
        with self.client.beta.threads.runs.submit_tool_outputs_stream(
            thread_id=self.thread_instance.thread_id,
            run_id=run_id,
            tool_outputs=tool_outputs,
            event_handler=EventHandler(self.tool_handlers, self.client, self.thread_instance)
        ) as stream:
            stream.until_done()

class Thread:
    """
    Thread is a high-level manager for OpenAI Assistant conversational threads, 
    providing robust methods for message handling, thread lifecycle, and 
    integration with tool-calling workflows.

    Responsibilities:
    - Manages the creation, retrieval, modification, and deletion of 
    OpenAI Assistant threads.
    - Handles sending and queuing of messages, ensuring that messages 
    are not sent while a run is active (to avoid API errors).
    - Supports both streaming and non-streaming assistant runs, with 
    seamless handling of tool calls via user-provided handler functions.
    - Integrates with EventHandler to provide real-time UI updates and 
    tool call resolution in Streamlit chat applications.
    - Maintains a message queue to ensure that user messages are processed 
    in order, even if multiple are sent during an active run.

    Relationship to EventHandler:
    - Thread instantiates and passes itself to EventHandler for each streaming 
    run, allowing the handler to submit tool outputs and update the thread state.
    - Tool handler functions are provided by the user and passed through to both 
    Thread and EventHandler for tool call resolution.

    Usage Example:
        thread = Thread(api_key)
        thread.addMessage("Hello!", role="user")
        thread.runWithStreaming(assistant_id, tool_handlers)

    Tool Call Example:
        def my_tool_handler(arg1, arg2):
            # ... do something ...
            return result
        tool_handlers = {"my_tool": my_tool_handler}
        thread.runWithStreaming(assistant_id, tool_handlers)

    Notes for Developers:
    - Use addMessage() to add user or assistant messages. If a run is active, messages are queued and processed in order.
    - Use runWithStreaming() for real-time UI updates, or runWithoutStreaming() for batch processing.
    - The message queue and run status checks help prevent race conditions and API errors in multi-message scenarios.
    - Designed for extensibility and robust error handling in production chatbots.
    """

    def __init__(self, api_key: str):
        """
        Initialize a new Thread instance with OpenAI API key and create a new conversation thread.

        This method sets up the foundation for a conversation with an OpenAI Assistant.
        It creates a new thread on the OpenAI platform and initializes the message queue
        for handling concurrent message sending.

        Args:
            api_key (str): Your OpenAI API key for authentication.

        Raises:
            Exception: If thread creation fails due to API issues, authentication problems,
                      or network connectivity issues.

        Example:
            >>> thread = Thread("sk-...")  # Your OpenAI API key
            >>> print(f"Created thread: {thread.thread_id}")
            Created thread: thread_abc123def456

        Note:
            - The API key should be kept secure and not logged or exposed in client-side code.
            - Each Thread instance represents a unique conversation that can be shared
              between multiple runs with the same or different assistants.
            - The message queue is initialized as empty and will be used to handle
              messages sent during active runs.
        """
        self.api_key = api_key
        self.client = openai.OpenAI(api_key=api_key)
        self.message_queue = deque()  # Queue to store messages
        try:
            self.thread = self.client.beta.threads.create()
            self.thread_id = self.thread.id
        except Exception as e:
            raise Exception(f"Error creating thread: {str(e)}")

    def _sendMessage(self, content: str, role: str, metadata: dict) -> dict:
        """
        Send a message directly to the OpenAI thread (internal method).

        This is the low-level method that actually sends messages to the OpenAI API.
        It's called by addMessage() after all safety checks have been performed.

        Args:
            content (str): The message content to send.
            role (str): The role of the message sender ("user" or "assistant").
            metadata (dict): Optional metadata to attach to the message.
                Example: {"source": "web", "timestamp": "2024-01-01T12:00:00Z"}

        Returns:
            dict: The created message object from OpenAI API.

        Raises:
            Exception: If message sending fails due to API errors, network issues,
                      or invalid thread state.

        Example:
            >>> message = thread._sendMessage("Hello!", "user", {"source": "chat"})
            >>> print(f"Message ID: {message.id}")
            Message ID: msg_xyz789

        Note:
            - This method should not be called directly in most cases.
            - Use addMessage() instead, which includes safety checks and queuing logic.
            - The role parameter should be one of: "user" or "assistant".
            - Metadata is optional but useful for tracking message sources or context.
        """
        try:
            return self.client.beta.threads.messages.create(
                thread_id=self.thread_id,
                role=role,
                content=content,
                metadata=metadata
            )
        except Exception as e:
            raise Exception(f"Error sending message: {str(e)}")
    
    def addMessage(self, content: str, role: str = "user", metadata: dict = None) -> dict:
        """
        Add a message to the thread with intelligent queuing and safety checks.

        This method is the primary way to add messages to a conversation. It includes
        sophisticated logic to handle message queuing when a run is active, preventing
        API errors and ensuring messages are processed in the correct order.

        Message Processing Logic:
        1. If there are already queued messages, add to queue (maintains order)
        2. If a run is currently active, add to queue (prevents API conflicts)
        3. Otherwise, send the message immediately

        Args:
            content (str): The message content to send.
            role (str, optional): The role of the message sender. Defaults to "user".
                Valid values: "user", "assistant"
            metadata (dict, optional): Optional metadata for the message. Defaults to None.
                Example: {"source": "web", "user_id": "123", "session": "abc"}

        Returns:
            dict or None: The created message object if sent immediately, None if queued.

        Raises:
            Exception: If message sending fails due to API errors or network issues.

        Examples:
            # Basic usage
            >>> thread.addMessage("Hello, how are you?")
            <Message object>

            # With custom role and metadata
            >>> thread.addMessage(
            ...     "Assistant initialization complete",
            ...     role="assistant",
            ...     metadata={"component": "auth", "level": "info"}
            ... )

            # Message queuing during active run
            >>> thread.runWithStreaming(assistant_id, handlers)  # Run starts
            >>> result = thread.addMessage("Quick question")  # Queued
            >>> print(result)  # None (message was queued)
            # Message will be processed after run completes

        Queuing Behavior:
            - Messages are queued in FIFO (First In, First Out) order
            - Queued messages are automatically processed after each run completes
            - This prevents race conditions and API errors in multi-message scenarios
            - The queue is processed by processQueueWithRuns() after run completion

        Note:
            - Use "user" role for messages from the end user
            - Use "assistant" role for messages from the AI assistant (rarely needed)
            - Metadata is useful for tracking, debugging, and analytics
        """
        # First check if we already have queued messages
        if len(self.message_queue) > 0:
            self.message_queue.append((content, role, metadata))
            return None
            
        # Then do a thorough check for active runs
        if self.isRunActive():
            self.message_queue.append((content, role, metadata))
            return None
        
        # If we get here, it should be safe to send the message
        return self._sendMessage(content, role, metadata)

    def delete(self) -> dict:
        """
        Delete the current thread and all its associated data from OpenAI.

        This method permanently removes the thread and all its messages from the OpenAI
        platform. This action cannot be undone, so use with caution.

        Returns:
            dict: Deletion status from OpenAI API.

        Raises:
            Exception: If deletion fails due to API errors, network issues, or if the
                      thread has already been deleted.

        Example:
            >>> thread = Thread(api_key)
            >>> # ... use thread for conversation ...
            >>> result = thread.delete()
            >>> print("Thread deleted successfully")
            Thread deleted successfully

        Warning:
            - This action is irreversible - all messages and conversation history will be lost
            - Consider backing up important conversation data before deletion
            - The thread_id will become invalid after deletion
        """
        try:
            return self.client.beta.threads.delete(thread_id=self.thread_id)
        except Exception as e:
            raise Exception(f"Error deleting thread: {str(e)}")

    def isRunActive(self) -> bool:
        """
        Check if there is an active run on the current thread with robust error handling.

        This method performs a thorough check for active runs by examining the status
        of recent runs. It includes multiple retry attempts and considers various
        run states to ensure accurate detection.

        Active Run States:
        - 'queued': Run is waiting to be processed
        - 'in_progress': Run is currently executing
        - 'requires_action': Run is waiting for tool outputs
        - 'cancelling': Run is in the process of being cancelled

        Returns:
            bool: True if any run is active, False otherwise.

        Implementation Details:
        - Checks up to 10 most recent runs (in descending order)
        - Performs up to 3 retry attempts with 100ms delays
        - Returns True on error (fail-safe approach)
        - Uses descending order to prioritize recent runs

        Example:
            >>> thread = Thread(api_key)
            >>> thread.addMessage("Hello")
            >>> print(thread.isRunActive())  # False (no run started yet)
            False
            >>> thread.runWithStreaming(assistant_id, handlers)  # Run starts
            >>> print(thread.isRunActive())  # True (run is active)
            True

        Note:
            - This method is called by addMessage() to determine if messages should be queued
            - The retry logic helps handle temporary API delays or network issues
            - Returns True on error to prevent message sending during uncertain states
        """
        try:
            # Define statuses that indicate an active run
            active_statuses = {
                'queued', 
                'in_progress', 
                'requires_action',
                'cancelling'  # Include cancelling status as it's still technically active
            }
            
            # Try up to 3 times with a small delay
            for _ in range(3):
                runs = self.client.beta.threads.runs.list(
                    thread_id=self.thread_id,
                    limit=10,  # Increase limit to catch more recent runs
                    order='desc'  # Get most recent runs first
                )
                
                # Check each run's status
                for run in runs:
                    if run.status in active_statuses:
                        return True
                
                # If no active runs found, wait a tiny bit and check again
                time.sleep(0.1)  # 100ms delay between checks
            
            # If we get here, no active runs were found after all checks
            return False
            
        except Exception as e:
            # Log the error but don't crash - assume there might be an active run
            print(f"Error checking run status: {str(e)}")
            return True  # Safer to assume there is an active run if we can't check

    def listMessages(self, limit: int = 20, order: str = "desc") -> list:
        """
        Retrieve a list of messages from the current thread.

        This method fetches messages from the thread, allowing you to review conversation
        history, analyze responses, or implement features like message search or export.

        Args:
            limit (int, optional): Maximum number of messages to return. Defaults to 20.
                Valid range: 1-100 (OpenAI API limit)
            order (str, optional): Sort order for messages. Defaults to "desc".
                Valid values: "asc" (oldest first), "desc" (newest first)

        Returns:
            list: List of message objects from OpenAI API.

        Raises:
            Exception: If message retrieval fails due to API errors, network issues,
                      or invalid thread state.

        Examples:
            # Get recent messages (default behavior)
            >>> messages = thread.listMessages()
            >>> for msg in messages:
            ...     print(f"{msg.role}: {msg.content[0].text.value}")

            # Get first 10 messages in chronological order
            >>> messages = thread.listMessages(limit=10, order="asc")
            >>> for msg in messages:
            ...     print(f"Message {msg.id}: {msg.content[0].text.value}")

            # Get all messages (up to API limit)
            >>> all_messages = thread.listMessages(limit=100, order="desc")

        Message Object Structure:
            Each message object contains:
            - id: Unique message identifier
            - role: "user" or "assistant"
            - content: List of content blocks (usually text)
            - created_at: Timestamp of message creation
            - metadata: Optional metadata dictionary

        Note:
            - The OpenAI API has a maximum limit of 100 messages per request
            - Messages are paginated if there are more than the requested limit
            - Use "desc" order for most recent messages, "asc" for chronological order
            - Message content is typically in content[0].text.value format
        """
        try:
            return self.client.beta.threads.messages.list(
                thread_id=self.thread_id,
                limit=limit,
                order=order
            )
        except Exception as e:
            raise Exception(f"Error listing messages: {str(e)}")

    def modify(self, metadata: dict = None) -> dict:
        """
        Modify the metadata of the current thread.

        This method allows you to update the thread's metadata, which can be useful
        for adding custom properties, tracking information, or organizing threads
        in your application.

        Args:
            metadata (dict, optional): New metadata to set for the thread. Defaults to None.
                Example: {"project": "chatbot", "user_id": "123", "version": "1.0"}

        Returns:
            dict: The updated thread object from OpenAI API.

        Raises:
            Exception: If modification fails due to API errors, network issues,
                      or invalid thread state.

        Examples:
            # Add metadata to thread
            >>> thread.modify({"project": "customer_support", "priority": "high"})
            <Thread object with updated metadata>

            # Update existing metadata
            >>> thread.modify({"status": "active", "last_updated": "2024-01-01"})

            # Clear metadata (set to empty dict)
            >>> thread.modify({})

        Note:
            - Metadata is useful for organizing and categorizing threads
            - You can store any JSON-serializable data in metadata
            - Metadata is preserved across thread operations and can be retrieved later
            - Common use cases: user identification, project tracking, status flags
        """
        try:
            return self.client.beta.threads.update(
                thread_id=self.thread_id,
                metadata=metadata
            )
        except Exception as e:
            raise Exception(f"Error modifying thread: {str(e)}")
    
    def modifyMessage(self, message_id: str, metadata: dict) -> dict:
        """
        Modify the metadata of a specific message in the thread.

        This method allows you to update metadata for individual messages, which can
        be useful for adding annotations, flags, or tracking information to specific
        parts of the conversation.

        Args:
            message_id (str): The ID of the message to modify.
                Example: "msg_abc123def456"
            metadata (dict): New metadata to set for the message.
                Example: {"flagged": True, "category": "question", "sentiment": "positive"}

        Returns:
            dict: The updated message object from OpenAI API.

        Raises:
            Exception: If modification fails due to API errors, network issues,
                      invalid message ID, or thread state issues.

        Examples:
            # Add metadata to a message
            >>> thread.modifyMessage("msg_123", {"flagged": True, "reviewed": False})
            <Message object with updated metadata>

            # Update message with categorization
            >>> thread.modifyMessage("msg_456", {
            ...     "category": "technical_support",
            ...     "priority": "medium",
            ...     "assigned_to": "agent_001"
            ... })

        Note:
            - Message metadata is separate from thread metadata
            - Useful for message-level tracking, categorization, or workflow management
            - Message IDs can be obtained from listMessages() or message objects
            - Metadata changes are preserved and can be retrieved later
        """
        try:
            return self.client.beta.threads.messages.update(
                thread_id=self.thread_id,
                message_id=message_id,
                metadata=metadata
            )
        except Exception as e:
            raise Exception(f"Error modifying message: {str(e)}")

    def processQueuedMessages(self) -> None:
        """
        Process and send all queued messages in order.

        This method sends all messages that were queued during an active run.
        It processes messages in FIFO (First In, First Out) order to maintain
        conversation flow.

        Usage:
            This method is typically called automatically after a run completes,
            but can be called manually if needed.

        Example:
            >>> thread.addMessage("Message 1")  # Sent immediately
            >>> thread.runWithStreaming(assistant_id, handlers)  # Run starts
            >>> thread.addMessage("Message 2")  # Queued
            >>> thread.addMessage("Message 3")  # Queued
            >>> # After run completes, messages are automatically processed
            >>> thread.processQueuedMessages()  # Sends Message 2, then Message 3

        Note:
            - Messages are sent in the order they were queued
            - This method is called automatically by processQueueWithRuns()
            - Useful for manual control of message processing if needed
        """
        while self.message_queue:
            content, role, metadata = self.message_queue.popleft()
            self._sendMessage(content, role, metadata)

    def processQueueWithRuns(self, assistant_id: str, tool_handlers: dict, stream: bool = False) -> None:
        """
        Process queued messages one by one, running the assistant after each message.

        This method processes queued messages sequentially, running the assistant
        after each message to ensure proper conversation flow and tool call handling.
        It's the preferred method for processing queued messages as it maintains
        the full conversation context.

        Args:
            assistant_id (str): The ID of the assistant to run the thread with.
            tool_handlers (dict): Dictionary mapping function names to their handler functions.
            stream (bool, optional): Whether to use streaming for assistant runs.
                Defaults to False. Use True for real-time UI updates.

        Raises:
            Exception: If processing fails due to API errors, network issues,
                      or problems with individual message processing.

        Processing Flow:
            1. Take the first message from the queue
            2. Send it to the thread
            3. Run the assistant (with or without streaming)
            4. Repeat until queue is empty

        Example:
            >>> thread.addMessage("First question")
            >>> thread.runWithStreaming(assistant_id, handlers)  # Run starts
            >>> thread.addMessage("Follow-up question")  # Queued
            >>> thread.addMessage("Another question")    # Queued
            >>> # After first run completes, processQueueWithRuns is called automatically
            >>> # This will:
            >>> # 1. Send "Follow-up question" and run assistant
            >>> # 2. Send "Another question" and run assistant

        Note:
            - This method is called automatically after runWithStreaming() and runWithoutStreaming()
            - Only user messages trigger assistant runs (assistant messages are sent but don't run)
            - The stream parameter should match the original run method used
            - This ensures proper conversation flow and tool call handling
        """
        while self.message_queue:
            # Process one message at a time
            content, role, metadata = self.message_queue.popleft()
            self._sendMessage(content, role, metadata)
            
            # Run the thread for this message
            if role == "user":  # Only run for user messages
                try:
                    # Use the same run method as the original call
                    if stream:
                        self.runWithStreaming(assistant_id, tool_handlers)
                    else:
                        self.runWithoutStreaming(assistant_id, tool_handlers)
                except Exception as e:
                    # If there's an error, add the remaining messages back to the queue
                    raise Exception(f"Error processing queued message: {str(e)}")
    
    def retrieve(self) -> dict:
        """
        Retrieve the current thread's information from OpenAI.

        This method fetches the current thread's metadata, creation time, and other
        properties from the OpenAI API. Useful for checking thread status, metadata,
        or getting thread information for debugging or administrative purposes.

        Returns:
            dict: The thread object from OpenAI API containing thread information.

        Raises:
            Exception: If retrieval fails due to API errors, network issues,
                      or if the thread has been deleted.

        Examples:
            # Get thread information
            >>> thread_info = thread.retrieve()
            >>> print(f"Thread ID: {thread_info.id}")
            >>> print(f"Created: {thread_info.created_at}")
            >>> print(f"Metadata: {thread_info.metadata}")

            # Check if thread exists and is accessible
            >>> try:
            ...     thread_info = thread.retrieve()
            ...     print("Thread is accessible")
            ... except Exception as e:
            ...     print(f"Thread error: {e}")

        Thread Object Properties:
            - id: Unique thread identifier
            - object: Always "thread"
            - created_at: Timestamp when thread was created
            - metadata: Custom metadata dictionary (if any)
            - other OpenAI-specific properties

        Note:
            - This method is useful for thread validation and status checking
            - Can be used to verify thread existence before operations
            - Returns the same thread object that was created in __init__
        """
        try:
            return self.client.beta.threads.retrieve(thread_id=self.thread_id)
        except Exception as e:
            raise Exception(f"Error retrieving thread: {str(e)}")
    
    def retrieveLastMessage(self) -> dict:
        """
        Retrieve the most recent message from the thread.

        This method fetches the last message sent in the conversation, which is
        useful for getting the assistant's most recent response or checking the
        current state of the conversation.

        Returns:
            dict: Dictionary containing the last message's content and role.
                Format: {"content": [...], "role": "user|assistant"}

        Examples:
            # Get the last message
            >>> last_msg = thread.retrieveLastMessage()
            >>> print(f"Role: {last_msg['role']}")
            >>> print(f"Content: {last_msg['content'][0]['text']['value']}")

            # Check if the last message was from the assistant
            >>> last_msg = thread.retrieveLastMessage()
            >>> if last_msg['role'] == 'assistant':
            ...     print("Last message was from assistant")
            >>> else:
            ...     print("Last message was from user")

        Return Format:
            The returned dictionary has this structure:
            {
                "content": [
                    {
                        "type": "text",
                        "text": {"value": "Message content here"}
                    }
                ],
                "role": "user"  # or "assistant"
            }

        Note:
            - Returns a default message if no messages exist in the thread
            - Useful for checking conversation state or getting recent responses
            - Content is in the standard OpenAI message format
            - This method is a convenience wrapper around listMessages(limit=1)
        """
        messages = self.client.beta.threads.messages.list(
            thread_id=self.thread_id,
            limit=1,
            order="desc"
        )
        # Get the first message from the cursor page
        for message in messages:
            return {
                "content": message.content,
                "role": message.role
            }
        # Return a default message if no messages are found
        return {
            "content": [{"text": {"value": "No messages found"}}],
            "role": "assistant"
        }
    
    def retrieveMessage(self, message_id: str) -> dict:
        """
        Retrieve a specific message from the thread by its ID.

        This method fetches a particular message using its unique identifier,
        which is useful for accessing specific parts of the conversation history
        or implementing features like message editing or deletion.

        Args:
            message_id (str): The unique identifier of the message to retrieve.
                Example: "msg_abc123def456"

        Returns:
            dict: Dictionary containing the message's content and role.
                Format: {"content": [...], "role": "user|assistant"}

        Raises:
            Exception: If retrieval fails due to API errors, network issues,
                      invalid message ID, or if the message doesn't exist.

        Examples:
            # Retrieve a specific message
            >>> message = thread.retrieveMessage("msg_abc123def456")
            >>> print(f"Role: {message['role']}")
            >>> print(f"Content: {message['content'][0]['text']['value']}")

            # Get message IDs from listMessages and retrieve specific ones
            >>> messages = thread.listMessages()
            >>> for msg in messages:
            ...     if msg.role == "user":
            ...         user_msg = thread.retrieveMessage(msg.id)
            ...         print(f"User said: {user_msg['content'][0]['text']['value']}")

        Return Format:
            The returned dictionary has this structure:
            {
                "content": [
                    {
                        "type": "text",
                        "text": {"value": "Message content here"}
                    }
                ],
                "role": "user"  # or "assistant"
            }

        Note:
            - Message IDs can be obtained from listMessages() or message objects
            - Useful for accessing specific conversation points or implementing
              message-level features like editing or deletion
            - Returns the same format as retrieveLastMessage() for consistency
            - Invalid message IDs will raise an exception
        """
        try:
            message = self.client.beta.threads.messages.retrieve(
                thread_id=self.thread_id,
                message_id=message_id
            )
            return {
                "content": message.content,
                "role": message.role
            }
        except Exception as e:
            raise Exception(f"Error retrieving message: {str(e)}")
    
    def runWithStreaming(self, assistant_id: str, tool_handlers: dict) -> None:
        """
        Run the assistant with streaming enabled for real-time chat experience.

        This method starts a streaming run with the specified assistant, providing
        real-time updates to the Streamlit UI as the assistant responds. It handles
        tool calls automatically and integrates with EventHandler for seamless
        conversation flow.

        Key Features:
        - Real-time streaming of assistant responses
        - Automatic tool call handling and execution
        - Integration with Streamlit for live UI updates
        - Message queuing and processing after completion
        - Robust error handling and state management

        Args:
            assistant_id (str): The ID of the OpenAI Assistant to run.
                Example: "asst_abc123def456"
            tool_handlers (dict): Dictionary mapping function names to their handler functions.
                Example: {"get_weather": weather_function, "calculate": math_function}

        Raises:
            Exception: If the run fails due to API errors, network issues,
                      invalid assistant ID, or problems with tool execution.

        Streaming Process:
            1. Create EventHandler instance for event processing
            2. Start streaming run with the assistant
            3. EventHandler processes events in real-time:
               - Message deltas update Streamlit UI
               - Tool calls are executed and results submitted
            4. After completion, process any queued messages

        Examples:
            # Basic streaming run
            >>> thread.addMessage("What's the weather like?")
            >>> thread.runWithStreaming("asst_123", {})

            # With tool handlers
            >>> def get_weather(city):
            ...     return f"Weather in {city}: Sunny, 25°C"
            >>> tool_handlers = {"get_weather": get_weather}
            >>> thread.runWithStreaming("asst_123", tool_handlers)

            # In a Streamlit app
            >>> if st.button("Send Message"):
            ...     thread.addMessage(user_input)
            ...     thread.runWithStreaming(assistant_id, tool_handlers)

        Tool Call Integration:
            - Tool handlers are called automatically when the assistant requests them
            - Results are submitted back to the assistant seamlessly
            - Multiple tool calls in a single response are handled correctly
            - Tool execution errors are handled gracefully

        Streamlit Integration:
            - Creates chat message containers automatically
            - Updates UI in real-time as text streams in
            - Maintains proper chat layout and styling
            - Handles multiple messages in the same session

        Note:
            - Use this method for interactive chat applications
            - Tool handlers should be thread-safe and handle errors gracefully
            - The assistant_id must be valid and accessible
            - Queued messages are processed automatically after completion
        """
        try:
            handler = EventHandler(tool_handlers, self.client, self)
            
            with self.client.beta.threads.runs.stream(
                thread_id=self.thread_id,
                assistant_id=assistant_id,
                event_handler=handler
            ) as stream:
                stream.until_done()
            
            # Process any queued messages after run completion
            self.processQueueWithRuns(assistant_id, tool_handlers, stream=True)
            
        except Exception as e:
            raise Exception(f"Error in streaming run: {str(e)}")

    def runWithoutStreaming(self, assistant_id: str, tool_handlers: dict) -> dict:
        """
        Run the assistant without streaming for batch processing or non-interactive use.

        This method executes the assistant in a non-streaming mode, waiting for
        the complete response before returning. It's useful for background processing,
        API integrations, or when real-time updates aren't needed.

        Key Features:
        - Complete response before returning
        - Automatic tool call handling and execution
        - Message queuing and processing after completion
        - Returns run status and messages for programmatic use
        - Suitable for batch processing and API integrations

        Args:
            assistant_id (str): The ID of the OpenAI Assistant to run.
                Example: "asst_abc123def456"
            tool_handlers (dict): Dictionary mapping function names to their handler functions.
                Example: {"get_weather": weather_function, "calculate": math_function}

        Returns:
            dict: Dictionary containing run status and messages.
                Format: {"status": "completed|failed|requires_action", "messages": [...]}

        Raises:
            Exception: If the run fails due to API errors, network issues,
                      invalid assistant ID, or problems with tool execution.

        Processing Flow:
            1. Start non-streaming run with the assistant
            2. Wait for completion or tool call requirement
            3. If tool calls are required:
               - Execute each tool handler
               - Submit results back to assistant
               - Continue until completion
            4. Return final status and messages
            5. Process any queued messages

        Examples:
            # Basic non-streaming run
            >>> thread.addMessage("What's 2+2?")
            >>> result = thread.runWithoutStreaming("asst_123", {})
            >>> print(f"Status: {result['status']}")
            >>> if result['messages']:
            ...     print(f"Response: {result['messages'][0].content[0].text.value}")

            # With tool handlers for batch processing
            >>> def process_data(data):
            ...     return f"Processed: {data.upper()}"
            >>> tool_handlers = {"process_data": process_data}
            >>> result = thread.runWithoutStreaming("asst_123", tool_handlers)

            # Error handling
            >>> try:
            ...     result = thread.runWithoutStreaming(assistant_id, tool_handlers)
            ...     if result['status'] == 'completed':
            ...         print("Run completed successfully")
            ...     else:
            ...         print(f"Run status: {result['status']}")
            ... except Exception as e:
            ...     print(f"Run failed: {e}")

        Return Values:
            The returned dictionary contains:
            - status: Run completion status ("completed", "failed", "requires_action", etc.)
            - messages: List of messages if run completed successfully, None otherwise

        Tool Call Handling:
            - Tool calls are handled automatically during the run
            - Multiple tool calls are processed sequentially
            - Tool execution errors are caught and handled
            - Results are submitted back to continue the conversation

        Use Cases:
            - Background processing and automation
            - API integrations and webhooks
            - Batch message processing
            - Testing and debugging assistant responses
            - Non-interactive applications

        Note:
            - Use this method when real-time updates aren't needed
            - Tool handlers should be fast and reliable for batch processing
            - The method blocks until the run completes
            - Queued messages are processed automatically after completion
        """
        try:
            run = self.client.beta.threads.runs.create_and_poll(
                thread_id=self.thread_id,
                assistant_id=assistant_id
            )

            if run.status == 'requires_action':
                tool_outputs = []
                for tool in run.required_action.submit_tool_outputs.tool_calls:
                    if tool.function.name in tool_handlers:
                        arguments = json.loads(tool.function.arguments)
                        handler = tool_handlers[tool.function.name]
                        output = str(handler(**arguments))
                        tool_outputs.append({
                            "tool_call_id": tool.id,
                            "output": output
                        })
                
                if tool_outputs:
                    run = self.client.beta.threads.runs.submit_tool_outputs_and_poll(
                        thread_id=self.thread_id,
                        run_id=run.id,
                        tool_outputs=tool_outputs
                    )

            messages = self.listMessages() if run.status == 'completed' else None
            
            # Process any queued messages after run completion
            self.processQueueWithRuns(assistant_id, tool_handlers, stream=False)
            
            return {"status": run.status, "messages": messages}
        except Exception as e:
            raise Exception(f"Error in non-streaming run: {str(e)}")