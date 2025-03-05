# API Documentation

This section provides detailed documentation for the Llama Stack APIs, including examples and best practices.

## Available API Guides

- [Agents API Guide](./agents_api_guide.md): Detailed guide for creating and interacting with agentic systems
- Inference API Guide (Coming Soon)
- Memory API Guide (Coming Soon)
- Safety API Guide (Coming Soon)
- Tools API Guide (Coming Soon)

## API Overview

Llama Stack provides a unified API layer for various AI capabilities:

### Agents API

The Agents API allows you to create and interact with agentic systems that can use tools, access memory, and follow safety guidelines. Key features include:

- Creating agents with specific instructions and capabilities
- Managing sessions to group related interactions
- Processing turns with messages and agent responses
- Executing tools and retrieving information from knowledge bases

See the [Agents API Guide](./agents_api_guide.md) for detailed examples and best practices.

### Inference API

The Inference API provides a unified interface for text and multimodal inference using Llama models. Key features include:

- Text completion and chat completion
- Image understanding and generation
- Streaming responses for long-running interactions
- Control over sampling parameters and response formats

### Memory API

The Memory API enables retrieval-augmented generation (RAG) capabilities. Key features include:

- Document storage and retrieval
- Vector embeddings for semantic search
- Context insertion for enhanced responses
- Integration with various vector databases

### Safety API

The Safety API provides tools for ensuring safe and responsible AI interactions. Key features include:

- Input and output filtering
- Content moderation
- Safety shields for agents
- Customizable safety policies

### Tools API

The Tools API allows you to extend agent capabilities with custom tools. Key features include:

- Tool definition and registration
- Tool execution and response handling
- Client-side and server-side tool execution
- Integration with agent workflows

## Best Practices

1. **Use descriptive names** for resources to make them easier to manage
2. **Provide clear instructions** to guide agent behavior
3. **Use streaming** for long-running interactions to improve user experience
4. **Clean up resources** when they're no longer needed
5. **Handle errors gracefully** by implementing proper exception handling
6. **Follow type annotations** to ensure correct API usage
7. **Refer to documentation** for detailed examples and best practices
