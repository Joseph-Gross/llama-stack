# Security Policy

## Reporting a Vulnerability

Please report vulnerabilities to our bug bounty program at https://bugbounty.meta.com/

## Security Best Practices

### API Security

1. **Authentication and Authorization**
   - Always use strong authentication mechanisms when deploying Llama Stack
   - Implement proper authorization checks for all API endpoints
   - Consider using OAuth 2.0 or API keys with appropriate scopes

2. **Input Validation**
   - All user inputs should be validated before processing
   - Use the built-in validation middleware for request validation
   - Validate both structure and content of JSON payloads

3. **Rate Limiting**
   - Configure appropriate rate limits using the `LLAMA_STACK_RATE_LIMIT` environment variable
   - Default rate limit is 100 requests per minute per client IP
   - Adjust based on your application's needs and expected traffic patterns

### Environment Variables

1. **Sensitive Data Handling**
   - Never hardcode API keys, passwords, or other secrets in your code
   - Use environment variables for all sensitive configuration
   - Consider using a secrets management solution for production deployments

2. **Environment Variable Format**
   - Use the `${env.VARIABLE_NAME}` syntax in configuration files
   - Provide defaults where appropriate: `${env.VARIABLE_NAME:default_value}`
   - Validate environment variables before use

### Deployment Security

1. **HTTPS Configuration**
   - Always use HTTPS in production environments
   - Configure TLS using the `--tls-keyfile` and `--tls-certfile` options
   - Use strong TLS configurations (TLS 1.2+, strong ciphers)

2. **Container Security**
   - Run containers with minimal privileges
   - Use non-root users inside containers
   - Keep base images and dependencies updated

3. **Network Security**
   - Restrict network access to Llama Stack servers
   - Use firewalls to limit incoming connections
   - Consider using a reverse proxy for additional security layers

### Model and Data Security

1. **Model Access Control**
   - Implement access controls for sensitive models
   - Consider data classification for different types of models
   - Monitor model usage for unusual patterns

2. **Data Processing**
   - Be cautious with user-provided data, especially when using code execution tools
   - Sanitize inputs to prevent injection attacks
   - Implement proper error handling to avoid information disclosure

3. **Output Filtering**
   - Use safety shields to filter potentially harmful outputs
   - Implement content moderation for user-facing applications
   - Consider implementing additional guardrails for sensitive use cases

## Security Features

Llama Stack includes several built-in security features:

1. **Security Headers Middleware**
   - Adds security-related HTTP headers to responses
   - Helps prevent common web vulnerabilities (XSS, clickjacking, etc.)
   - Enabled by default in all server deployments

2. **CORS Middleware**
   - Controls cross-origin resource sharing
   - Prevents unauthorized cross-origin requests
   - Configurable for specific origins if needed

3. **Rate Limiting**
   - Protects against abuse and DoS attacks
   - Configurable via environment variables
   - Tracks requests by client IP address

4. **Input Validation**
   - Validates request structure and content
   - Prevents malformed requests from being processed
   - Limits request size to prevent resource exhaustion

5. **Secure Error Handling**
   - Prevents sensitive information disclosure in error messages
   - Provides appropriate error responses for different error types
   - Logs detailed errors server-side while limiting client-side information

## Security Maintenance

1. **Dependency Management**
   - Regularly update dependencies to address security vulnerabilities
   - Use tools like `pip-audit` to check for known vulnerabilities
   - Follow a structured process for dependency updates

2. **Security Testing**
   - Implement security-focused tests for critical components
   - Consider regular security assessments or penetration testing
   - Use automated scanning tools as part of your CI/CD pipeline

3. **Incident Response**
   - Develop an incident response plan for security issues
   - Establish clear communication channels for security incidents
   - Document and learn from security incidents
