# Security Policy

## Reporting a Vulnerability

Please report vulnerabilities to our bug bounty program at https://bugbounty.meta.com/

## Security Best Practices

When deploying Llama Stack in production environments, especially in financial services contexts, please follow these security guidelines:

### Authentication and Authorization
- Always implement proper authentication for API endpoints
- Use environment variables for storing sensitive credentials
- Never hardcode passwords, API keys, or tokens in the codebase
- Implement proper role-based access control for different API operations

### Data Protection
- Encrypt sensitive data at rest and in transit
- Use HTTPS for all API communications
- Implement proper data validation for all inputs
- Sanitize user inputs to prevent injection attacks
- Validate URLs to prevent SSRF (Server-Side Request Forgery) attacks

### Network Security
- Configure CORS properly to restrict cross-origin requests
- Use firewalls to limit access to the server
- Implement rate limiting to prevent DoS attacks
- Use secure WebSockets for streaming connections
- Block access to internal networks and localhost from remote URLs

### Deployment Security
- Keep dependencies updated to avoid known vulnerabilities
- Run with minimal privileges
- Use container security best practices
- Implement proper logging and monitoring
- Use secure defaults for all configuration options

### Compliance Considerations
- Ensure GDPR compliance for user data
- Follow financial services industry regulations
- Implement audit logging for sensitive operations
- Regularly perform security assessments
- Document all security measures for compliance audits

## Security Features

Llama Stack includes several security features:
- Content safety shields (LlamaGuard, CodeScanner)
- Input validation mechanisms
- Parameterized SQL queries
- URL validation utilities
- Secure error handling to prevent information disclosure
- Header validation to prevent injection attacks

For more information on implementing security best practices with Llama Stack, please refer to the documentation.
