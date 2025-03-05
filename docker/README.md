# Docker Setup for Llama Stack

This directory contains Docker configuration files for running Llama Stack in a containerized environment.

## Prerequisites

- Docker
- Docker Compose

## Quick Start

To start the Llama Stack application:

```bash
# Navigate to the docker directory
cd docker

# Build and start the containers
docker-compose up
```

This will start the Llama Stack application on http://localhost:8000.

## Available Services

The `docker-compose.yml` file defines several services:

- **llama-stack**: Runs the main application with hot-reloading enabled
- **tests**: Runs the test suite
- **lint**: Runs linting checks

## Running Tests

To run the test suite:

```bash
docker-compose run tests
```

## Running Linting

To run linting checks:

```bash
docker-compose run lint
```

## Building a Custom Image

To build a custom Docker image:

```bash
docker build -t llama-stack:custom -f docker/Dockerfile .
```

## Customizing the Environment

You can customize the environment by modifying the `docker-compose.yml` file. For example, to change the port mapping:

```yaml
ports:
  - "8080:8000"  # Map container port 8000 to host port 8080
```

## Troubleshooting

### Common Issues

1. **Port Conflicts**: If you encounter port conflicts, change the port mapping in the `docker-compose.yml` file.

2. **Permission Issues**: If you encounter permission issues with mounted volumes, you may need to adjust the permissions of the mounted directories.

3. **Memory Issues**: If the container runs out of memory, you can increase the memory limit in the `docker-compose.yml` file:

   ```yaml
   services:
     llama-stack:
       deploy:
         resources:
           limits:
             memory: 4G
   ```

### Getting Help

If you encounter any issues that aren't covered here, please open an issue on the GitHub repository.
