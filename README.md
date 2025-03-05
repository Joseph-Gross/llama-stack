# Llama Stack

[![PyPI version](https://img.shields.io/pypi/v/llama_stack.svg)](https://pypi.org/project/llama_stack/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/llama-stack)](https://pypi.org/project/llama-stack/)
[![License](https://img.shields.io/pypi/l/llama_stack.svg)](https://github.com/meta-llama/llama-stack/blob/main/LICENSE)
[![Discord](https://img.shields.io/discord/1257833999603335178)](https://discord.gg/llama-stack)

[**Quick Start**](https://llama-stack.readthedocs.io/en/latest/getting_started/index.html) | [**Documentation**](https://llama-stack.readthedocs.io/en/latest/index.html) | [**Colab Notebook**](./docs/getting_started.ipynb) | [**Research Examples**](./docs/examples/README.md) | [**Reproducibility Guide**](./docs/preprocessing/reproducibility_checklist.md)

Llama Stack standardizes the core building blocks that simplify AI application development. It codifies best practices across the Llama ecosystem, with a strong focus on reproducibility, robustness, and responsible AI development. More specifically, it provides:

- **Unified API layer** for Inference, RAG, Agents, Tools, Safety, Evals, and Telemetry.
- **Plugin architecture** to support the rich ecosystem of different API implementations in various environments, including local development, on-premises, cloud, and mobile.
- **Prepackaged verified distributions** which offer a one-stop solution for developers to get started quickly and reliably in any environment.
- **Multiple developer interfaces** like CLI and SDKs for Python, Typescript, iOS, and Android.
- **Standalone applications** as examples for how to build production-grade AI applications with Llama Stack.
- **Research-focused tools** for ensuring reproducibility, comprehensive documentation, and robust error handling in AI research projects.
- **Interdisciplinary collaboration support** through standardized interfaces and clear documentation that researchers from different domains can understand.

<div style="text-align: center;">
  <img
    src="https://github.com/user-attachments/assets/33d9576d-95ea-468d-95e2-8fa233205a50"
    width="480"
    title="Llama Stack"
    alt="Llama Stack"
  />
</div>

### Llama Stack Benefits
- **Flexible Options**: Developers can choose their preferred infrastructure without changing APIs and enjoy flexible deployment choices.
- **Consistent Experience**: With its unified APIs, Llama Stack makes it easier to build, test, and deploy AI applications with consistent application behavior.
- **Robust Ecosystem**: Llama Stack is already integrated with distribution partners (cloud providers, hardware vendors, and AI-focused companies) that offer tailored infrastructure, software, and services for deploying Llama models.
- **Research Reproducibility**: Built-in tools for ensuring reproducible AI research, including seed management, comprehensive logging, and standardized data processing pipelines.
- **Interdisciplinary Collaboration**: Clear interfaces and documentation that enable researchers from different domains to collaborate effectively on AI projects.
- **Responsible AI Development**: Integrated safety mechanisms and best practices that align with human-centered AI principles.

By reducing friction and complexity, Llama Stack empowers developers and researchers to focus on what they do best: building transformative and responsible generative AI applications and conducting reproducible research.

### API Providers
Here is a list of the various API providers and available distributions that can help developers get started easily with Llama Stack. 

| **API Provider Builder** |    **Environments**    | **Agents** | **Inference** | **Memory** | **Safety** | **Telemetry** |
|:------------------------:|:----------------------:|:----------:|:-------------:|:----------:|:----------:|:-------------:|
|      Meta Reference      |      Single Node       |     ✅      |       ✅       |     ✅      |     ✅      |       ✅       |
|        SambaNova         |         Hosted         |            |       ✅       |            |            |               |
|         Cerebras         |         Hosted         |            |       ✅       |            |            |               |
|        Fireworks         |         Hosted         |     ✅      |       ✅       |     ✅      |            |               |
|       AWS Bedrock        |         Hosted         |            |       ✅       |            |     ✅      |               |
|         Together         |         Hosted         |     ✅      |       ✅       |            |     ✅      |               |
|           Groq           |         Hosted         |            |       ✅       |            |            |               |
|          Ollama          |      Single Node       |            |       ✅       |            |            |               |
|           TGI            | Hosted and Single Node |            |       ✅       |            |            |               |
|        NVIDIA NIM        | Hosted and Single Node |            |       ✅       |            |            |               |
|          Chroma          |      Single Node       |            |               |     ✅      |            |               |
|        PG Vector         |      Single Node       |            |               |     ✅      |            |               |
|    PyTorch ExecuTorch    |     On-device iOS      |     ✅      |       ✅       |            |            |               |
|           vLLM           | Hosted and Single Node |            |       ✅       |            |            |               |

### Distributions

A Llama Stack Distribution (or "distro") is a pre-configured bundle of provider implementations for each API component. Distributions make it easy to get started with a specific deployment scenario - you can begin with a local development setup (eg. ollama) and seamlessly transition to production (eg. Fireworks) without changing your application code. Here are some of the distributions we support:

|               **Distribution**                |                                                                    **Llama Stack Docker**                                                                     |                                                 Start This Distribution                                                  |
|:---------------------------------------------:|:-------------------------------------------------------------------------------------------------------------------------------------------------------------:|:------------------------------------------------------------------------------------------------------------------------:|
|                Meta Reference                 |           [llamastack/distribution-meta-reference-gpu](https://hub.docker.com/repository/docker/llamastack/distribution-meta-reference-gpu/general)           |      [Guide](https://llama-stack.readthedocs.io/en/latest/distributions/self_hosted_distro/meta-reference-gpu.html)      |
|           Meta Reference Quantized            | [llamastack/distribution-meta-reference-quantized-gpu](https://hub.docker.com/repository/docker/llamastack/distribution-meta-reference-quantized-gpu/general) | [Guide](https://llama-stack.readthedocs.io/en/latest/distributions/self_hosted_distro/meta-reference-quantized-gpu.html) |
|                   SambaNova                   |                     [llamastack/distribution-sambanova](https://hub.docker.com/repository/docker/llamastack/distribution-sambanova/general)                     |   [Guide](https://llama-stack.readthedocs.io/en/latest/distributions/self_hosted_distro/sambanova.html)   |
|                   Cerebras                    |                     [llamastack/distribution-cerebras](https://hub.docker.com/repository/docker/llamastack/distribution-cerebras/general)                     |   [Guide](https://llama-stack.readthedocs.io/en/latest/distributions/self_hosted_distro/cerebras.html)   |
|                    Ollama                     |                       [llamastack/distribution-ollama](https://hub.docker.com/repository/docker/llamastack/distribution-ollama/general)                       |            [Guide](https://llama-stack.readthedocs.io/en/latest/distributions/self_hosted_distro/ollama.html)            |
|                      TGI                      |                          [llamastack/distribution-tgi](https://hub.docker.com/repository/docker/llamastack/distribution-tgi/general)                          |             [Guide](https://llama-stack.readthedocs.io/en/latest/distributions/self_hosted_distro/tgi.html)              |
|                   Together                    |                     [llamastack/distribution-together](https://hub.docker.com/repository/docker/llamastack/distribution-together/general)                     |           [Guide](https://llama-stack.readthedocs.io/en/latest/distributions/self_hosted_distro/together.html)           |
|                   Fireworks                   |                    [llamastack/distribution-fireworks](https://hub.docker.com/repository/docker/llamastack/distribution-fireworks/general)                    |          [Guide](https://llama-stack.readthedocs.io/en/latest/distributions/self_hosted_distro/fireworks.html)           |
| vLLM |                  [llamastack/distribution-remote-vllm](https://hub.docker.com/repository/docker/llamastack/distribution-remote-vllm/general)                  |         [Guide](https://llama-stack.readthedocs.io/en/latest/distributions/self_hosted_distro/remote-vllm.html)          |

### Installation

You have several ways to install this repository:

* **Install as a package**:
   You can install the repository directly from [PyPI](https://pypi.org/project/llama-stack/) by running the following command:
   ```bash
   pip install llama-stack
   ```

* **Install from source**:
   If you prefer to install from the source code, we recommend using [uv](https://github.com/astral-sh/uv).
   Then, run the following commands:
   ```bash
    git clone git@github.com:meta-llama/llama-stack.git
    cd llama-stack

    uv sync
    uv pip install -e .
   ```

* **Using the setup script**:
   For a more automated setup, use the provided setup script:
   ```bash
   git clone https://github.com/meta-llama/llama-stack.git
   cd llama-stack
   
   chmod +x setup.sh
   ./setup.sh
   ```

* **Using Docker**:
   For a containerized setup:
   ```bash
   git clone https://github.com/meta-llama/llama-stack.git
   cd llama-stack/docker
   
   docker-compose up
   ```

For detailed installation instructions, including environment setup for interdisciplinary collaboration, see [INSTALLATION.md](INSTALLATION.md) and [SETUP.md](SETUP.md).

### Documentation

Please checkout our [Documentation](https://llama-stack.readthedocs.io/en/latest/index.html) page for more details.

* **Setup and Installation**
    * [Installation Guide](INSTALLATION.md): Detailed instructions for installing Llama Stack in various environments.
    * [Setup Guide](SETUP.md): Instructions for setting up the development environment.
    * [Docker Setup](docker/README.md): Guide for using Docker to run Llama Stack in a containerized environment.

* **CLI References**
    * [llama (server-side) CLI Reference](https://llama-stack.readthedocs.io/en/latest/references/llama_cli_reference/index.html): Guide for using the `llama` CLI to work with Llama models (download, study prompts), and building/starting a Llama Stack distribution.
    * [llama (client-side) CLI Reference](https://llama-stack.readthedocs.io/en/latest/references/llama_stack_client_cli_reference.html): Guide for using the `llama-stack-client` CLI, which allows you to query information about the distribution.

* **Getting Started**
    * [Quick guide to start a Llama Stack server](https://llama-stack.readthedocs.io/en/latest/getting_started/index.html).
    * [Jupyter notebook](./docs/getting_started.ipynb) to walk-through how to use simple text and vision inference llama_stack_client APIs
    * The complete Llama Stack lesson [Colab notebook](https://colab.research.google.com/drive/1dtVmxotBsI4cGZQNsJRYPrLiDeT0Wnwt) of the new [Llama 3.2 course on Deeplearning.ai](https://learn.deeplearning.ai/courses/introducing-multimodal-llama-3-2/lesson/8/llama-stack).
    * A [Zero-to-Hero Guide](https://github.com/meta-llama/llama-stack/tree/main/docs/zero_to_hero_guide) that guide you through all the key components of llama stack with code samples.

* **Research and Reproducibility**
    * [Example Notebooks](./docs/examples/README.md): Comprehensive examples demonstrating reproducible research workflows.
    * [Reproducibility Checklist](./docs/preprocessing/reproducibility_checklist.md): Guidelines for ensuring reproducible AI research.
    * [Data Preprocessing Documentation](./docs/preprocessing/README.md): Detailed documentation on data preprocessing steps.
    * [Vector Database Operations](./docs/preprocessing/vector_database_operations.md): Guide for working with vector databases in research contexts.
    * [Embedding Generation](./docs/preprocessing/embedding_generation.md): Documentation on generating and managing embeddings.
    * [Document Chunking](./docs/preprocessing/document_chunking.md): Guide for effective document chunking strategies.

* **Contributing**
    * [Contributing Guide](CONTRIBUTING.md): Guidelines for contributing to the project.
    * [Adding a new API Provider](https://llama-stack.readthedocs.io/en/latest/contributing/new_api_provider.html) to walk-through how to add a new API provider.

### Llama Stack Client SDKs

|  **Language** |  **Client SDK** | **Package** |
| :----: | :----: | :----: |
| Python |  [llama-stack-client-python](https://github.com/meta-llama/llama-stack-client-python) | [![PyPI version](https://img.shields.io/pypi/v/llama_stack_client.svg)](https://pypi.org/project/llama_stack_client/)
| Swift  | [llama-stack-client-swift](https://github.com/meta-llama/llama-stack-client-swift) | [![Swift Package Index](https://img.shields.io/endpoint?url=https%3A%2F%2Fswiftpackageindex.com%2Fapi%2Fpackages%2Fmeta-llama%2Fllama-stack-client-swift%2Fbadge%3Ftype%3Dswift-versions)](https://swiftpackageindex.com/meta-llama/llama-stack-client-swift)
| Typescript   | [llama-stack-client-typescript](https://github.com/meta-llama/llama-stack-client-typescript) | [![NPM version](https://img.shields.io/npm/v/llama-stack-client.svg)](https://npmjs.org/package/llama-stack-client)
| Kotlin | [llama-stack-client-kotlin](https://github.com/meta-llama/llama-stack-client-kotlin) | [![Maven version](https://img.shields.io/maven-central/v/com.llama.llamastack/llama-stack-client-kotlin)](https://central.sonatype.com/artifact/com.llama.llamastack/llama-stack-client-kotlin)

Check out our client SDKs for connecting to a Llama Stack server in your preferred language, you can choose from [python](https://github.com/meta-llama/llama-stack-client-python), [typescript](https://github.com/meta-llama/llama-stack-client-typescript), [swift](https://github.com/meta-llama/llama-stack-client-swift), and [kotlin](https://github.com/meta-llama/llama-stack-client-kotlin) programming languages to quickly build your applications.

You can find more example scripts with client SDKs to talk with the Llama Stack server in our [llama-stack-apps](https://github.com/meta-llama/llama-stack-apps/tree/main/examples) repo.

## Research and Interdisciplinary Collaboration

Llama Stack is designed to support interdisciplinary research collaboration with a focus on reproducibility, robust error handling, and comprehensive documentation:

### Reproducibility Features

- **Random Seed Management**: Utilities for consistent random number generation across different libraries (NumPy, PyTorch, Python's random).
- **Comprehensive Logging**: Detailed logging of all operations for transparency and debugging.
- **Standardized Data Processing**: Consistent approaches to document chunking, embedding generation, and vector database operations.
- **Configuration Management**: Tools for explicit configuration management and versioning.

### Robust Error Handling

- **Type Validation**: Runtime type checking with Pydantic for early error detection.
- **Graceful Failure Recovery**: Mechanisms for handling unexpected inputs and recovering from errors.
- **Comprehensive Exception Handling**: Detailed error messages and appropriate fallback behaviors.

### Interdisciplinary Collaboration Support

- **Clear Documentation**: Comprehensive docstrings and guides accessible to researchers from different domains.
- **Example Notebooks**: Ready-to-use examples demonstrating key workflows and best practices.
- **Standardized Interfaces**: Consistent APIs that abstract away implementation details.

### Human-Centered AI Principles

- **Safety Mechanisms**: Built-in safety shields and content filtering capabilities.
- **Transparency**: Clear documentation of model capabilities and limitations.
- **Responsible Deployment**: Guidelines for responsible AI deployment and usage.

By providing these features, Llama Stack enables researchers from diverse disciplines to collaborate effectively on AI projects, ensuring that research is reproducible, robust, and aligned with responsible AI principles.
