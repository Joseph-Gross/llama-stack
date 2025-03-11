# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.

from datetime import datetime
from enum import Enum
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, validator


class TransactionType(Enum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRANSFER = "transfer"
    PAYMENT = "payment"
    REFUND = "refund"


class TransactionStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REVERSED = "reversed"
    HELD = "held"


class Currency(Enum):
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    BRL = "BRL"
    JPY = "JPY"


class TransactionDetails(BaseModel):
    """Model for transaction details with comprehensive validation."""
    transaction_id: str = Field(..., description="Unique identifier for the transaction")
    amount: float = Field(..., gt=0, description="Transaction amount (must be positive)")
    currency: Currency = Field(..., description="Currency code for the transaction")
    timestamp: datetime = Field(..., description="Transaction timestamp in ISO format")
    account_number: str = Field(..., min_length=8, max_length=20, description="Account number")
    transaction_type: TransactionType = Field(..., description="Type of transaction")
    status: TransactionStatus = Field(..., description="Current status of the transaction")
    description: Optional[str] = Field(None, max_length=200, description="Transaction description")

    @validator("account_number")
    def validate_account_number(cls, v):
        if not v.isalnum():
            raise ValueError("Account number must contain only alphanumeric characters")
        return v


class ComplianceCheckResult(BaseModel):
    """Model for compliance check results."""
    is_kyc_verified: bool = Field(..., description="Whether KYC verification is complete")
    risk_score: float = Field(..., ge=0, le=100, description="Risk score (0-100)")
    transaction_limit_exceeded: bool = Field(..., description="Whether transaction exceeds limits")
    suspicious_activity_detected: bool = Field(..., description="Whether suspicious activity was detected")
    compliance_status: Literal["approved", "rejected", "review_required"] = Field(
        ..., description="Overall compliance status"
    )
    reason_codes: Optional[List[str]] = Field(None, description="Reason codes for compliance decision")


class FraudDetectionResult(BaseModel):
    """Model for fraud detection results."""
    fraud_score: float = Field(..., ge=0, le=100, description="Fraud score (0-100)")
    is_fraudulent: bool = Field(..., description="Whether the transaction is likely fraudulent")
    confidence: float = Field(..., ge=0, le=1, description="Confidence in the fraud determination")
    detection_rules_triggered: List[str] = Field(..., description="List of triggered detection rules")
    recommended_action: Literal["approve", "deny", "review"] = Field(
        ..., description="Recommended action based on fraud analysis"
    )


class AccountSummary(BaseModel):
    """Model for account summary information."""
    account_id: str = Field(..., description="Unique identifier for the account")
    account_type: Literal["checking", "savings", "credit", "investment"] = Field(
        ..., description="Type of account"
    )
    balance: float = Field(..., description="Current account balance")
    currency: Currency = Field(..., description="Currency of the account")
    available_credit: Optional[float] = Field(None, description="Available credit for credit accounts")
    interest_rate: Optional[float] = Field(None, ge=0, description="Interest rate for the account")
    account_status: Literal["active", "inactive", "frozen", "closed"] = Field(
        ..., description="Current status of the account"
    )
    last_transaction_date: Optional[datetime] = Field(None, description="Date of last transaction")
