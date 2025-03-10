# Llama Stack Security Guide

This guide provides detailed information about security considerations when using Llama Stack. It covers best practices, built-in security features, and recommendations for secure deployment.

## Security Architecture

Llama Stack implements a layered security approach:

1. **Network Layer Security**: HTTPS, firewalls, and network isolation
2. **Application Layer Security**: Input validation, authentication, and authorization
3. **Data Layer Security**: Encryption, access controls, and data handling policies
4. **Model Layer Security**: Model access controls and output filtering

## Security Features

### Security Middleware

Llama Stack includes several security middleware components:

#### Security Headers Middleware

The `SecurityHeadersMiddleware` adds the following security headers to all responses:

- `X-Content-Type-Options: nosniff` - Prevents MIME type sniffing
- `X-Frame-Options: DENY` - Prevents clickjacking attacks
- `Content-Security-Policy` - Controls resource loading
- `Strict-Transport-Security` - Enforces HTTPS
- `X-XSS-Protection` - Helps prevent XSS attacks
- `Referrer-Policy` - Controls referrer information
- `Cache-Control` and `Pragma` - Controls caching behavior

Example configuration:

```python
from fastapi import FastAPI
from llama_stack.distribution.server.server import SecurityHeadersMiddleware

app = FastAPI()
app.add_middleware(SecurityHeadersMiddleware)
```

#### CORS Middleware

The `CORSMiddleware` controls cross-origin resource sharing:

- Configures allowed origins, methods, and headers
- Handles preflight OPTIONS requests
- Prevents unauthorized cross-origin requests

Example configuration:

```python
from fastapi import FastAPI
from llama_stack.distribution.server.server import CORSMiddleware

app = FastAPI()
app.add_middleware(CORSMiddleware)
```

#### Rate Limiting Middleware

The `RateLimitMiddleware` protects against abuse and DoS attacks:

- Limits requests per client IP address
- Configurable rate limit and time window
- Returns 429 status code when limit is exceeded

Example configuration:

```python
import os
from fastapi import FastAPI
from llama_stack.distribution.server.server import RateLimitMiddleware

# Set rate limit via environment variable
os.environ["LLAMA_STACK_RATE_LIMIT"] = "100"  # 100 requests per minute

app = FastAPI()
app.add_middleware(RateLimitMiddleware)
```

### Input Validation

Llama Stack implements comprehensive input validation:

- Request size limits to prevent DoS attacks
- JSON structure validation
- Parameter validation for API endpoints

The validation system is implemented in `llama_stack.distribution.server.validation` and integrated into the request handling pipeline.

### Secure Error Handling

The error handling system is designed to prevent information disclosure:

- Sanitizes error messages to remove sensitive information
- Provides appropriate HTTP status codes
- Logs detailed errors server-side while limiting client-side information

### Environment Variable Security

Llama Stack includes secure environment variable handling:

- Redaction of sensitive information in logs and output
- Support for default values
- Validation of environment variable format and content

## Security Best Practices

### Authentication and Authorization

While Llama Stack doesn't include built-in authentication, we recommend:

1. Implementing API key authentication for all endpoints
2. Using OAuth 2.0 for user-facing applications
3. Implementing role-based access control for different APIs

Example using a simple API key middleware:

```python
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.base import BaseHTTPMiddleware

class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        api_key = request.headers.get("X-API-Key")
        if not api_key or api_key != os.environ.get("API_KEY"):
            raise HTTPException(status_code=403, detail="Invalid API key")
        return await call_next(request)

app = FastAPI()
app.add_middleware(APIKeyMiddleware)
```

### Secure Deployment

For secure deployment, consider:

1. **Container Security**:
   - Use minimal base images
   - Run as non-root user
   - Implement resource limits

2. **Network Security**:
   - Use a reverse proxy (e.g., Nginx, Traefik)
   - Implement network policies
   - Use firewalls to restrict access

3. **Secrets Management**:
   - Use a secrets management solution (e.g., HashiCorp Vault, AWS Secrets Manager)
   - Rotate credentials regularly
   - Implement least privilege access

### Model Security

For model security:

1. **Access Controls**:
   - Implement model-specific access controls
   - Consider different access levels for different models

2. **Output Filtering**:
   - Use safety shields to filter outputs
   - Implement content moderation
   - Consider domain-specific filtering

3. **Monitoring**:
   - Monitor model usage patterns
   - Implement alerting for unusual behavior
   - Audit model access and usage

## Security Checklist

Use this checklist when deploying Llama Stack:

- [ ] Enable HTTPS with valid certificates
- [ ] Configure security middleware (headers, CORS, rate limiting)
- [ ] Implement authentication and authorization
- [ ] Set appropriate rate limits
- [ ] Secure environment variables and secrets
- [ ] Implement network security controls
- [ ] Configure model access controls
- [ ] Implement output filtering
- [ ] Set up monitoring and alerting
- [ ] Develop an incident response plan
- [ ] Regularly update dependencies
- [ ] Conduct security testing

## Additional Resources

- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [FastAPI Security Documentation](https://fastapi.tiangolo.com/tutorial/security/)
