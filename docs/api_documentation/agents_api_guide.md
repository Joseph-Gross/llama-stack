# Agents API Guide

This guide provides detailed information on using the Agents API in Llama Stack, including examples and best practices.

## Overview

The Agents API allows you to create and interact with agentic systems that can use tools, access memory, and follow safety guidelines. The API provides a unified interface for creating agents, managing sessions, and processing turns.

## Key Concepts

- **Agent**: An AI assistant configured with specific instructions and capabilities
- **Session**: A conversation thread that groups related interactions with an agent
- **Turn**: A single interaction within a session, consisting of messages and agent responses
- **Step**: A discrete action taken by an agent during a turn (e.g., inference, tool execution)

## Creating an Agent

To create a new agent, you need to provide an `AgentConfig` object that specifies the model, instructions, and optional tools:

```python
from llama_stack_client import LlamaStackClient
from llama_stack_client.apis.agents import AgentConfig

# Initialize the client
client = LlamaStackClient("http://localhost:8000")

# Create an agent configuration
agent_config = AgentConfig(
    model="llama-3-70b-instruct",
    instructions="You are a helpful assistant that provides concise answers.",
    name="Research Assistant"
)

# Create the agent
response = await client.agents.create_agent(agent_config)
agent_id = response.agent_id

print(f"Created agent with ID: {agent_id}")
```

## Creating a Session

Once you have an agent, you can create a session to group related interactions:

```python
# Create a session
response = await client.agents.create_agent_session(
    agent_id=agent_id,
    session_name="Research Project"
)
session_id = response.session_id

print(f"Created session with ID: {session_id}")
```

## Interacting with an Agent

To interact with an agent, you create turns within a session:

```python
from llama_stack_client.apis.agents import UserMessage

# Send a message to the agent
response = await client.agents.create_agent_turn(
    agent_id=agent_id,
    session_id=session_id,
    messages=[UserMessage(content="What are the key components of a research paper?")]
)

# Process the response
turn = response
print(f"Agent response: {turn.response}")

# Continue the conversation
response = await client.agents.create_agent_turn(
    agent_id=agent_id,
    session_id=session_id,
    messages=[UserMessage(content="How should I structure the methodology section?")]
)

turn = response
print(f"Agent response: {turn.response}")
```

## Using Tools with Agents

Agents can use tools to perform actions or retrieve information:

```python
from llama_stack_client.apis.agents import AgentToolGroup, ToolDef

# Define a calculator tool
calculator_tool = ToolDef(
    name="calculator",
    description="Perform mathematical calculations",
    parameters={
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "The mathematical expression to evaluate"
            }
        },
        "required": ["expression"]
    }
)

# Create a tool group
tool_group = AgentToolGroup(
    name="math_tools",
    tools=[calculator_tool]
)

# Create a turn with tools
response = await client.agents.create_agent_turn(
    agent_id=agent_id,
    session_id=session_id,
    messages=[UserMessage(content="Calculate 25 * 16")],
    toolgroups=[tool_group]
)

# Process the response
turn = response
print(f"Agent response: {turn.response}")
```

## Streaming Responses

For long-running agent interactions, you can stream the response:

```python
# Create a turn with streaming enabled
stream = await client.agents.create_agent_turn(
    agent_id=agent_id,
    session_id=session_id,
    messages=[UserMessage(content="Write a summary of quantum computing")],
    stream=True
)

# Process the stream
async for chunk in stream:
    event = chunk.event
    if event.event_type == "turn_progress":
        print(f"Progress: {event.payload.delta}", end="", flush=True)
    elif event.event_type == "turn_complete":
        print("\nTurn complete!")
```

## Retrieving Session History

You can retrieve the history of a session:

```python
# Get session details
session = await client.agents.get_agents_session(
    agent_id=agent_id,
    session_id=session_id
)

# Print turn history
for turn in session.turns:
    print(f"Turn {turn.id}:")
    print(f"  User: {turn.messages[0].content}")
    print(f"  Agent: {turn.response}")
    print()
```

## Cleaning Up

When you're done with a session or agent, you can delete them:

```python
# Delete a session
await client.agents.delete_agents_session(
    agent_id=agent_id,
    session_id=session_id
)

# Delete an agent
await client.agents.delete_agent(
    agent_id=agent_id
)
```

## Best Practices

1. **Use descriptive names** for agents and sessions to make them easier to manage
2. **Provide clear instructions** to guide agent behavior
3. **Use streaming** for long-running interactions to improve user experience
4. **Clean up resources** by deleting sessions and agents when they're no longer needed
5. **Handle errors gracefully** by implementing proper exception handling

## Error Handling

```python
try:
    response = await client.agents.create_agent_turn(
        agent_id=agent_id,
        session_id=session_id,
        messages=[UserMessage(content="What's the weather like today?")]
    )
except Exception as e:
    print(f"Error creating turn: {e}")
    # Handle the error appropriately
```

## Advanced Usage

### Using Memory for RAG

Agents can use memory to retrieve information from knowledge bases:

```python
from llama_stack_client.apis.agents import Document

# Provide documents to the agent
documents = [
    Document(
        content="Quantum computing uses quantum bits or qubits...",
        mime_type="text/plain"
    )
]

# Create a turn with documents
response = await client.agents.create_agent_turn(
    agent_id=agent_id,
    session_id=session_id,
    messages=[UserMessage(content="Explain quantum computing")],
    documents=documents
)

# Process the response
turn = response
print(f"Agent response: {turn.response}")
```

### Resuming Turns with Tool Responses

When a turn requires client-side tool execution, you can resume it with the tool responses:

```python
from llama_stack_client.apis.agents import ToolResponseMessage

# Create a turn that might use tools
response = await client.agents.create_agent_turn(
    agent_id=agent_id,
    session_id=session_id,
    messages=[UserMessage(content="What's 123 * 456?")],
    toolgroups=[tool_group],
    allow_turn_resume=True
)

# If the turn is awaiting input
if response.status == "awaiting_input":
    # Execute the tool on the client side
    tool_call = response.steps[-1].tool_calls[0]
    expression = tool_call.arguments["expression"]
    result = eval(expression)  # In a real app, use a safer evaluation method
    
    # Resume the turn with the tool response
    tool_response = ToolResponseMessage(
        tool_call_id=tool_call.id,
        content=str(result)
    )
    
    resumed_response = await client.agents.resume_agent_turn(
        agent_id=agent_id,
        session_id=session_id,
        turn_id=response.id,
        tool_responses=[tool_response]
    )
    
    # Process the resumed response
    turn = resumed_response
    print(f"Agent response after tool execution: {turn.response}")
```
