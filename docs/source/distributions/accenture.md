# Accenture AI Provider

This distribution uses Accenture AI for LLM inference.

## Configuration

The Accenture AI provider requires an API key to access the service. You can set this in your environment:

```bash
export ACCENTURE_API_KEY=your_api_key_here
```

Or provide it in the provider data header when making requests:

```json
{
  "accenture_api_key": "your_api_key_here"
}
```

## Available Models

The following models are available through the Accenture AI provider:

- `accenture/accenture-llm-large` - Mapped to Llama 3.1 70B Instruct
- `accenture/accenture-llm-base` - Mapped to Llama 3.1 8B Instruct
- `accenture/accenture-embedding-model` - Embedding model with 768 dimensions

## Features

- Text generation (completion)
- Chat completion with tool support
- Embeddings generation
- Streaming responses
- Multimodal content support

## Example Usage

```python
from llama_stack_client import LlamaStackClient

client = LlamaStackClient(
    base_url="http://localhost:5001",
    api_key="your_api_key_here",
)

# Chat completion
response = client.inference.chat_completion(
    model_id="accenture/accenture-llm-large",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Tell me about Accenture's AI capabilities."},
    ],
)
print(response.completion_message.content)

# Embeddings
embeddings = client.inference.embeddings(
    model_id="accenture/accenture-embedding-model",
    contents=["Accenture is a global professional services company."],
)
print(embeddings.embeddings[0][:5])  # Print first 5 dimensions
```
