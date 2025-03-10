# Aliseda Inmobiliaria Custom LIA Chatbot Integration

This example demonstrates how to build a custom Language Intelligence Assistant (LIA) chatbot for a real estate company (Aliseda Inmobiliaria) using the Llama Stack framework.

## Overview

The application consists of:

1. **FastAPI Backend**: Integrates with Llama Stack to provide real estate-specific chatbot functionality
2. **React Frontend**: A modern UI for interacting with the chatbot and displaying property suggestions

## Features

- Real-time chat interface with the LIA chatbot
- Property search functionality using natural language
- Property filtering by type, location, and price range
- Display of property suggestions based on user queries
- Responsive design for desktop and mobile

## Architecture

The application uses:

- **Llama Stack Client**: For connecting to Llama Stack and creating custom agents
- **Custom Tools**: A property search tool that demonstrates how to extend Llama Stack with domain-specific functionality
- **FastAPI**: For the backend API endpoints
- **React + Tailwind CSS + shadcn/ui**: For the frontend UI components

## Getting Started

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd aliseda_backend
   ```

2. Install dependencies:
   ```bash
   poetry install
   ```

3. Create a `.env` file based on `.env.example` and configure your Llama Stack connection.

4. Start the backend server:
   ```bash
   poetry run fastapi dev app/main.py
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd aliseda_frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

4. Build for production:
   ```bash
   npm run build
   ```

## Implementation Details

### Custom Agent Creation

The backend creates a custom Llama Stack agent with real estate-specific tools and system prompt:

```python
agent_config = AgentConfig(
    system_prompt="""You are a helpful real estate assistant for Aliseda Inmobiliaria, a leading real estate company in Spain.
    Your goal is to help users find properties that match their needs and answer questions about real estate in Spain.
    You can search for properties using the property_search tool.
    Always be professional, helpful, and provide detailed information about properties when available.
    If you don't know something, admit it and offer to help in other ways.
    """,
    model=LLAMA_MODEL_NAME,
    tools=[property_search_tool]
)
```

### Property Search Tool

A custom tool is implemented to search for properties based on user queries:

```python
property_search_tool = Tool(
    name="property_search",
    description="Search for properties based on criteria like location, type, price range",
    parameters={
        "query": {
            "type": "string",
            "description": "The search query for properties (e.g., 'apartments in Madrid', 'villas with pool')"
        }
    }
)
```

## Extending This Example

You can extend this example by:

1. Connecting to a real property database instead of using sample data
2. Adding more specialized tools for mortgage calculation, neighborhood information, etc.
3. Implementing user authentication and saved searches
4. Adding multi-language support for international customers

## License

This example is part of the Llama Stack project and is subject to the same license terms.
