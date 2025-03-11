# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.

import pytest
from pydantic import TypeAdapter

from llama_stack.apis.inference import (
    ChatCompletionResponse,
    JsonSchemaResponseFormat,
    Message,
)
from llama_stack.providers.tests.test_cases.financial_services_models import (
    TransactionDetails,
    ComplianceCheckResult,
    FraudDetectionResult,
    AccountSummary,
)
from llama_stack.providers.tests.test_cases.test_case import TestCase

# How to run this test:
#
# pytest -v -s llama_stack/providers/tests/inference/test_financial_services.py
#   -m "(fireworks or ollama) and llama_3b"


class TestFinancialServices:
    @pytest.mark.parametrize(
        "test_case",
        [
            "inference:financial_services:transaction_validation",
        ],
    )
    @pytest.mark.asyncio(loop_scope="session")
    async def test_transaction_validation(self, inference_model, inference_stack, common_params, test_case):
        """Test transaction validation with structured output."""
        inference_impl, _ = inference_stack

        tc = TestCase(test_case)
        messages = [TypeAdapter(Message).validate_python(m) for m in tc["messages"]]

        response = await inference_impl.chat_completion(
            model_id=inference_model,
            messages=messages,
            stream=False,
            response_format=JsonSchemaResponseFormat(
                json_schema=TransactionDetails.model_json_schema(),
            ),
            **common_params,
        )

        assert isinstance(response, ChatCompletionResponse)
        assert response.completion_message.role == "assistant"
        assert isinstance(response.completion_message.content, str)

        # Validate the structured output against our model
        transaction = TransactionDetails.model_validate_json(response.completion_message.content)
        expected = tc["expected"]
        
        # Verify key fields match expected values
        assert transaction.transaction_id is not None
        assert transaction.amount == expected["amount"]
        assert transaction.currency.value == expected["currency"]
        assert transaction.account_number == expected["account_number"]
        assert transaction.transaction_type.value == expected["transaction_type"]
        assert transaction.status.value == expected["status"]

    @pytest.mark.parametrize(
        "test_case",
        [
            "inference:financial_services:compliance_check",
        ],
    )
    @pytest.mark.asyncio(loop_scope="session")
    async def test_compliance_check(self, inference_model, inference_stack, common_params, test_case):
        """Test compliance check with structured output."""
        inference_impl, _ = inference_stack

        tc = TestCase(test_case)
        messages = [TypeAdapter(Message).validate_python(m) for m in tc["messages"]]

        response = await inference_impl.chat_completion(
            model_id=inference_model,
            messages=messages,
            stream=False,
            response_format=JsonSchemaResponseFormat(
                json_schema=ComplianceCheckResult.model_json_schema(),
            ),
            **common_params,
        )

        assert isinstance(response, ChatCompletionResponse)
        assert response.completion_message.role == "assistant"
        assert isinstance(response.completion_message.content, str)

        # Validate the structured output against our model
        compliance_result = ComplianceCheckResult.model_validate_json(response.completion_message.content)
        expected = tc["expected"]
        
        # Verify key fields match expected values
        assert compliance_result.is_kyc_verified == expected["is_kyc_verified"]
        assert abs(compliance_result.risk_score - expected["risk_score"]) < 10  # Allow some variance
        assert compliance_result.transaction_limit_exceeded == expected["transaction_limit_exceeded"]
        assert compliance_result.suspicious_activity_detected == expected["suspicious_activity_detected"]
        assert compliance_result.compliance_status == expected["compliance_status"]

    @pytest.mark.parametrize(
        "test_case",
        [
            "inference:financial_services:fraud_detection",
        ],
    )
    @pytest.mark.asyncio(loop_scope="session")
    async def test_fraud_detection(self, inference_model, inference_stack, common_params, test_case):
        """Test fraud detection with structured output."""
        inference_impl, _ = inference_stack

        tc = TestCase(test_case)
        messages = [TypeAdapter(Message).validate_python(m) for m in tc["messages"]]

        response = await inference_impl.chat_completion(
            model_id=inference_model,
            messages=messages,
            stream=False,
            response_format=JsonSchemaResponseFormat(
                json_schema=FraudDetectionResult.model_json_schema(),
            ),
            **common_params,
        )

        assert isinstance(response, ChatCompletionResponse)
        assert response.completion_message.role == "assistant"
        assert isinstance(response.completion_message.content, str)

        # Validate the structured output against our model
        fraud_result = FraudDetectionResult.model_validate_json(response.completion_message.content)
        expected = tc["expected"]
        
        # Verify key fields match expected values
        assert abs(fraud_result.fraud_score - expected["fraud_score"]) < 10  # Allow some variance
        assert fraud_result.is_fraudulent == expected["is_fraudulent"]
        assert abs(fraud_result.confidence - expected["confidence"]) < 0.2  # Allow some variance
        
        # Check that at least the expected rules were triggered (model may add more)
        for rule in expected["detection_rules_triggered"]:
            assert rule in fraud_result.detection_rules_triggered
            
        assert fraud_result.recommended_action == expected["recommended_action"]

    @pytest.mark.parametrize(
        "test_case",
        [
            "inference:financial_services:account_summary",
        ],
    )
    @pytest.mark.asyncio(loop_scope="session")
    async def test_account_summary(self, inference_model, inference_stack, common_params, test_case):
        """Test account summary with structured output."""
        inference_impl, _ = inference_stack

        tc = TestCase(test_case)
        messages = [TypeAdapter(Message).validate_python(m) for m in tc["messages"]]

        response = await inference_impl.chat_completion(
            model_id=inference_model,
            messages=messages,
            stream=False,
            response_format=JsonSchemaResponseFormat(
                json_schema=AccountSummary.model_json_schema(),
            ),
            **common_params,
        )

        assert isinstance(response, ChatCompletionResponse)
        assert response.completion_message.role == "assistant"
        assert isinstance(response.completion_message.content, str)

        # Validate the structured output against our model
        account_summary = AccountSummary.model_validate_json(response.completion_message.content)
        expected = tc["expected"]
        
        # Verify key fields match expected values
        assert account_summary.account_id == expected["account_id"]
        assert account_summary.account_type == expected["account_type"]
        assert abs(account_summary.balance - expected["balance"]) < 10  # Allow some variance
        assert account_summary.currency.value == expected["currency"]
        assert account_summary.account_status == expected["account_status"]
