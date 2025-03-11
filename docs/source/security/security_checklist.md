# Security Checklist

Use this checklist to ensure your Llama Stack deployment follows security best practices.

## Pre-Deployment Checklist

### Dependency Security
- [ ] Run dependency vulnerability scan
- [ ] Update all dependencies to latest secure versions
- [ ] Lock dependency versions

### Configuration Security
- [ ] Enable TLS with valid certificates
- [ ] Configure rate limiting
- [ ] Set up appropriate CORS restrictions
- [ ] Enable security headers
- [ ] Configure input validation
- [ ] Set up API key authentication
- [ ] Enable appropriate safety shields

### Code Security
- [ ] Run static code analysis
- [ ] Review custom code for security issues
- [ ] Ensure no secrets are hardcoded
- [ ] Validate all user input
- [ ] Implement proper error handling

## Operational Security

### Monitoring
- [ ] Set up logging for security events
- [ ] Monitor for rate limit violations
- [ ] Track safety shield violations
- [ ] Set up alerts for suspicious activity

### Maintenance
- [ ] Schedule regular dependency updates
- [ ] Plan for certificate rotation
- [ ] Implement API key rotation
- [ ] Update safety shields as new versions become available

### Incident Response
- [ ] Document security incident response procedures
- [ ] Establish communication channels for security issues
- [ ] Define roles and responsibilities for security incidents
- [ ] Test incident response procedures
