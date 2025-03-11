# Financial Services API Testing in Llama Stack

This document describes the test patterns and scenarios for financial services APIs in Llama Stack.

## Overview

The financial services test suite demonstrates how to use Llama Stack for banking and financial applications with a focus on:

- Transaction validation and processing
- Compliance and regulatory checks
- Fraud detection and prevention
- Account information management
- Financial data security

## Test Models

The test suite uses the following Pydantic models for structured output validation:

- `TransactionDetails`: Validates transaction information
- `ComplianceCheckResult`: Validates compliance check results
- `FraudDetectionResult`: Validates fraud detection analysis
- `AccountSummary`: Validates account information

## Test Scenarios

### Transaction Validation

Tests the ability to extract and validate transaction details from user input, ensuring:

- Correct transaction amounts and currencies
- Valid account numbers
- Proper transaction types and statuses
- Timestamp validation

### Compliance Checks

Tests regulatory compliance verification, including:

- KYC (Know Your Customer) verification
- Risk scoring
- Transaction limit monitoring
- Suspicious activity detection

### Fraud Detection

Tests the ability to analyze transactions for potential fraud:

- Fraud scoring
- Confidence assessment
- Detection rule triggering
- Action recommendations

### Account Information

Tests the retrieval and validation of account information:

- Account identification
- Balance and currency information
- Account status verification
- Transaction history access

### Safety and Security

Tests the protection of sensitive financial information:

- Detection of PII (Personally Identifiable Information)
- Blocking of credit card and account numbers
- Prevention of fraud instruction requests
- Filtering of malicious financial queries

## Running the Tests

To run the financial services tests:

```bash
# Run all financial services tests
pytest -v -s llama_stack/providers/tests/inference/test_financial_services.py

# Run specific test scenarios
pytest -v -s llama_stack/providers/tests/inference/test_financial_services.py::TestFinancialServices::test_transaction_validation
pytest -v -s llama_stack/providers/tests/inference/test_financial_services.py::TestFinancialServices::test_compliance_check

# Run safety tests
pytest -v -s tests/client-sdk/safety/test_financial_safety.py
```

## Test Case Configuration

Test cases are defined in JSON files located at:
`llama_stack/providers/tests/test_cases/inference/financial_services.json`

Each test case includes:
- System and user messages that simulate a financial services interaction
- Expected output values for validation

## Integration with Existing Test Infrastructure

The financial services tests leverage Llama Stack's existing test infrastructure:
- Pydantic models for structured output validation
- JSON schema generation for response format specification
- Parametrized testing for multiple scenarios
- Provider-agnostic test execution

## Security Considerations

The test suite includes specific tests for financial security concerns:
- Protection of sensitive financial data (account numbers, credit card information)
- Detection of fraud-related queries
- Compliance with financial regulations
- Prevention of malicious instructions

## Extending the Test Suite

To add new financial services test scenarios:

1. Define new Pydantic models in `financial_services_models.py`
2. Add test cases to `financial_services.json`
3. Implement test methods in `test_financial_services.py`
4. Update safety tests as needed in `test_financial_safety.py`

## Best Practices

When developing financial services tests:

- Include comprehensive validation for all financial data fields
- Test both positive and negative scenarios
- Ensure compliance with financial regulations
- Implement robust security checks
- Test across multiple providers to ensure consistent behavior
