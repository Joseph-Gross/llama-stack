# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.

import pytest
from pydantic import BaseModel

from llama_stack.providers.tests.test_cases.test_case import TestCase


class TransactionDetails(BaseModel):
    """Model for transaction details."""
    transaction_id: str
    amount: float
    currency: str
    account_number: str
    transaction_type: str
    status: str


class ComplianceCheckResult(BaseModel):
    """Model for compliance check results."""
    is_kyc_verified: bool
    risk_score: float
    transaction_limit_exceeded: bool
    suspicious_activity_detected: bool
    compliance_status: str


@pytest.mark.parametrize(
    "test_case",
    [
        "inference:financial_services:transaction_validation",
    ],
)
def test_transaction_validation(client_with_models, text_model_id, test_case):
    """Test transaction validation with structured output."""
    tc = TestCase(test_case)

    response = client_with_models.inference.chat_completion(
        model_id=text_model_id,
        messages=tc["messages"],
        response_format={
            "type": "json_schema",
            "json_schema": TransactionDetails.model_json_schema(),
        },
        stream=False,
    )
    
    transaction = TransactionDetails.model_validate_json(response.completion_message.content)
    expected = tc["expected"]
    
    # Verify key fields match expected values
    assert transaction.transaction_id is not None
    assert transaction.amount == expected["amount"]
    assert transaction.currency == expected["currency"]
    assert transaction.account_number == expected["account_number"]
    assert transaction.transaction_type == expected["transaction_type"]
    assert transaction.status == expected["status"]


@pytest.mark.parametrize(
    "test_case",
    [
        "inference:financial_services:compliance_check",
    ],
)
def test_compliance_check(client_with_models, text_model_id, test_case):
    """Test compliance check with structured output."""
    tc = TestCase(test_case)

    response = client_with_models.inference.chat_completion(
        model_id=text_model_id,
        messages=tc["messages"],
        response_format={
            "type": "json_schema",
            "json_schema": ComplianceCheckResult.model_json_schema(),
        },
        stream=False,
    )
    
    compliance_result = ComplianceCheckResult.model_validate_json(response.completion_message.content)
    expected = tc["expected"]
    
    # Verify key fields match expected values
    assert compliance_result.is_kyc_verified == expected["is_kyc_verified"]
    assert abs(compliance_result.risk_score - expected["risk_score"]) < 10  # Allow some variance
    assert compliance_result.transaction_limit_exceeded == expected["transaction_limit_exceeded"]
    assert compliance_result.suspicious_activity_detected == expected["suspicious_activity_detected"]
    assert compliance_result.compliance_status == expected["compliance_status"]
