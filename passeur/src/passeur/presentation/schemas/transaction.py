"""
Transaction operation schemas.

Mirrors Node.js bridge API contract for transaction submission and status.
"""

from typing import Optional

from pydantic import BaseModel, Field


class SubmitTransactionRequest(BaseModel):
    """
    Request to submit signed transaction to blockchain.

    Corresponds to: POST /transaction/submit
    """

    signedTransaction: str = Field(
        ...,
        description="Base64 encoded signed transaction",
    )


class SubmitTransactionResponse(BaseModel):
    """
    Response from transaction submission.

    Contains transaction signature for tracking.
    """

    success: bool = Field(..., description="Submission success status")
    signature: str = Field(..., description="Transaction signature")


class TransactionStatusResponse(BaseModel):
    """
    Response from GET /transaction/status/{signature}.

    Returns transaction confirmation status.
    """

    success: bool = Field(..., description="Query success status")
    confirmed: bool = Field(..., description="Transaction confirmed flag")
    confirmationStatus: Optional[str] = Field(
        None,
        description="Confirmation level (processed/confirmed/finalized)",
    )
    slot: Optional[int] = Field(None, description="Slot number")
    err: Optional[dict] = Field(None, description="Error details if failed")
    status: Optional[str] = Field(
        None,
        description="Status for special cases (invalid_signature/not_found)",
    )
