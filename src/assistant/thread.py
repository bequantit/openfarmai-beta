import json, time
import openai
import streamlit as st
from typing_extensions import override
from openai import AssistantEventHandler
from collections import deque

from openfarma.src.params import BOT_CHAT_COLUMNS, AVATAR_BOT_PATH

class EventHandler(AssistantEventHandler):
    """
    Event handler for OpenAI Assistant events.

    Attributes:
        tool_handlers: Dictionary mapping function names to their handler functions
        client: The OpenAI client
        thread_instance: Reference to the Thread instance

    Methods:
        on_event: Handles the event
        handleRequiresAction: Handles the requires_action event
        submitToolOutputs: Submits tool outputs
    """
    def __init__(self, tool_handlers, client, thread_instance):
        super().__init__()
        self.tool_handlers = tool_handlers
        self.client = client
        self.thread_instance = thread_instance

    @override
    def on_event(self, event):
        """Handle other events like function calling"""
        if event.event == 'thread.run.requires_action':
            run_id = event.data.id
            self.thread_instance.requires_action_occurred = True
            self.handleRequiresAction(event.data, run_id)
        elif event.event == 'thread.run.completed':
            if self.thread_instance.requires_action_occurred:
                self.thread_instance.force_stream = False
            else:
                self.thread_instance.force_stream = True
    
    def handleRequiresAction(self, data, run_id):
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
        Submit tool outputs to the thread.
        """
        with self.client.beta.threads.runs.submit_tool_outputs_stream(
            thread_id=self.thread_instance.thread_id,
            run_id=run_id,
            tool_outputs=tool_outputs,
            event_handler=EventHandler(self.tool_handlers, self.client, self.thread_instance)
        ) as stream:
            if self.thread_instance.requires_action_occurred and (not self.thread_instance.force_stream):
                left, _ = st.columns(BOT_CHAT_COLUMNS)
                with left:
                    with st.chat_message("assistant", avatar=AVATAR_BOT_PATH):
                        container = st.empty()
                        current_text = ""
                        for chunk in stream.text_deltas:
                            current_text += chunk
                            current_text_styled = f'<div class="chat-message bot-message">{current_text}</div>'
                            container.write(current_text_styled, unsafe_allow_html=True)
                            time.sleep(0.03)

class Thread:
    """
    Class to manage OpenAI thread operations.

    Provides methods to create, retrieve, modify and delete threads, as well as
    manage messages within threads and handle runs with or without streaming.

    Attributes:
        api_key: The OpenAI API key
        client: The OpenAI client
        thread_id: The ID of the current thread
        message_queue: A queue to store messages
        requires_action_occurred: Indicates if a requires_action event has occurred
        force_stream: Indicates if streaming is forced

    Methods:
        __init__: Initializes the Thread class with the OpenAI API Key and creates a new thread.
        _sendMessage: Sends a message to the current thread.
        addMessage: Adds a message to the current thread or queues it if a run is active.
        delete: Deletes the current thread.
        isRunActive: Checks if there is an active run on the current thread.
        listMessages: Lists messages in the current thread.
        modify: Modifies the current thread's metadata.
        modifyMessage: Modifies a message's metadata in the current thread.
        processQueuedMessages: Processes and sends all queued messages once the run is completed.
        processQueueWithRuns: Processes queued messages one by one, running the thread after each message.
        retrieve: Retrieves the current thread.
        retrieveLastMessage: Retrieves the last message from the current thread.
        retrieveMessage: Retrieves a specific message from the current thread.
        runWithStreaming: Runs the thread with streaming enabled and handles tool calls.
        runWithoutStreaming: Runs the thread without streaming and handles tool calls.

    Example:
        >>> thread = Thread("your-api-key")
        >>> thread.addMessage("Hello, how are you?", "user")
        >>> thread.runWithStreaming("asst_123", handlers)
    
    Note:
        The ``runWithStreaming`` method is used for streaming responses, while ``runWithoutStreaming`` is used for non-streaming responses.
    """

    def __init__(self, api_key: str):
        """
        Initializes the Thread class with the OpenAI API Key and creates a new thread.

        Args:
            api_key (str): The OpenAI API key

        Example:
            >>> thread = Thread("your-api-key")
        """
        self.api_key = api_key
        self.client = openai.OpenAI(api_key=api_key)
        self.message_queue = deque()  # Queue to store messages
        self.requires_action_occurred = False
        self.force_stream = False
        try:
            self.thread = self.client.beta.threads.create()
            self.thread_id = self.thread.id
        except Exception as e:
            raise Exception(f"Error creating thread: {str(e)}")

    def _sendMessage(self, content: str, role: str, metadata: dict) -> dict:
        """
        Sends a message to the current thread.

        Args:
            content (str): Content of the message
            role (str): Role of the message sender
            metadata (dict, optional): Optional metadata for the message

        Returns:
            Created message object

        Raises:
            Exception: If there's an error sending the message
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
        Adds a message to the current thread or queues it if a run is active.
        Includes additional checks and retries for thread status.

        Args:
            content (str): Content of the message
            role (str, optional): Role of the message sender (default: "user")
            metadata (dict, optional): Optional metadata for the message

        Returns:
            Created message object or None if queued

        Raises:
            Exception: If there's an error adding the message
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
        Deletes the current thread.

        Args:
            None

        Returns:
            Deletion status

        Raises:
            Exception: If there's an error deleting the thread
        
        Example:
            >>> thread = Thread("your-api-key")
            >>> response = thread.delete()
            >>> print("Thread deleted successfully")
        """
        try:
            return self.client.beta.threads.delete(thread_id=self.thread_id)
        except Exception as e:
            raise Exception(f"Error deleting thread: {str(e)}")

    def isRunActive(self) -> bool:
        """
        Thoroughly checks if there is an active run on the current thread.
        Includes multiple status checks and a small delay to ensure accuracy.

        :return: True if any run is active, False otherwise
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
        Lists messages in the current thread.

        Args:
            limit (int, optional): Maximum number of messages to return
            order (str, optional): Sort order ("asc" or "desc")

        Returns:
            List of messages

        Raises:
            Exception: If there's an error listing messages
        
        Example:
            >>> thread = Thread("your-api-key")
            >>> messages = thread.listMessages()
            >>> for msg in messages:
            ...     print(f"{msg.role}: {msg.content}")
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
        Modifies the current thread's metadata.

        Args:
            metadata (dict, optional): Optional metadata to modify

        Returns:
            Modified thread object

        Raises:
            Exception: If there's an error modifying the thread
        
        Example:
            >>> thread = Thread("your-api-key")
            >>> modified = thread.modify({"key": "value"})
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
        Modifies a message's metadata in the current thread.

        Args:
            message_id (str): ID of the message to modify
            metadata (dict): New metadata for the message

        Returns:
            Modified message object

        Raises:
            Exception: If there's an error modifying the message
        
        Example:
            >>> thread = Thread("your-api-key")
            >>> modified = thread.modifyMessage("msg_xyz789", {"key": "value"})
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
        Processes and sends all queued messages once the run is completed.
        """
        while self.message_queue:
            content, role, metadata = self.message_queue.popleft()
            self._sendMessage(content, role, metadata)

    def processQueueWithRuns(self, assistant_id: str, tool_handlers: dict, stream: bool = False) -> None:
        """
        Processes queued messages one by one, running the thread after each message.
        
        Args:
            assistant_id (str): ID of the assistant to run the thread with
            tool_handlers (dict): Dictionary mapping function names to their handler functions
            stream (bool, optional): Whether to stream the run
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
        Retrieves the current thread.

        Args:
            None

        Returns:
            Thread object

        Raises:
            Exception: If there's an error retrieving the thread
        
        Example:
            >>> thread = Thread("your-api-key")
            >>> retrieved_thread = thread.retrieve()
        """
        try:
            return self.client.beta.threads.retrieve(thread_id=self.thread_id)
        except Exception as e:
            raise Exception(f"Error retrieving thread: {str(e)}")
    
    def retrieveLastMessage(self) -> dict:
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
        Retrieves a specific message from the current thread.

        Args:
            message_id (str): ID of the message to retrieve

        Returns:
            Message object with content and role

        Raises:
            Exception: If there's an error retrieving the message
        
        Example:
            >>> thread = Thread("your-api-key")
            >>> message = thread.retrieveMessage("msg_xyz789")
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
        Runs the thread with streaming enabled and handles tool calls.
        After completion, processes any queued messages.

        Args:
            assistant_id (str): ID of the assistant to run the thread with
            tool_handlers (dict): Dictionary mapping function names to their handler functions

        Raises:
            Exception: If there's an error during the run
        """
        try:
            # Reset thread state before starting new run
            self.requires_action_occurred = False
            self.force_stream = False
            
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
        Runs the thread without streaming and handles tool calls.
        After completion, processes any queued messages.

        Args:
            assistant_id (str): ID of the assistant to run the thread with
            tool_handlers (dict): Dictionary mapping function names to their handler functions

        Returns:
            Final run status and messages

        Raises:
            Exception: If there's an error during the run
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