from typing import Literal, Optional

from pydantic import BaseModel, Field

YesNo = Literal["Yes", "No"]


class CaseExtraction(BaseModel):
    """Structured information extracted from a customer complaint document."""

    customer_name: str = Field(description="Full name of the customer")
    email: Optional[str] = Field(default=None, description="Customer email address, null if not present")
    phone_number: Optional[str] = Field(default=None, description="Customer phone number, null if not present")
    product_or_service: Optional[str] = Field(default=None, description="Product or service involved")
    complaint_category: Literal[
        "Billing", "Product Defect", "Delivery", "Service Quality",
        "Technical Issue", "Refund", "Account", "Other",
    ] = Field(description="Best-fitting complaint category")
    issue_description: str = Field(description="Short description of the issue, based only on the document")
    resolution_provided: Optional[str] = Field(default=None, description="Resolution given so far, null if none")
    is_complaint: YesNo = Field(
        description="Yes only if the customer expresses dissatisfaction or reports a problem; "
                    "No for general enquiries, information requests or service requests"
    )
    escalation_required: YesNo = Field(description="Yes if the document indicates escalation is needed or done")
    supporting_document_available: YesNo = Field(description="Yes if receipts, photos, invoices etc. are mentioned as attached")
    case_status: Literal["Open", "In Progress", "Resolved", "Escalated", "Closed"] = Field(
        description="Overall current status of the case"
    )


class CaseSummary(BaseModel):
    """Internal management summary for a case."""

    case_overview: str = Field(description="One or two sentence overview of the case")
    key_issue: str = Field(description="The core problem")
    action_taken: str = Field(description="Actions taken so far")
    current_status: str = Field(description="Current status of the case")
    recommended_next_action: str = Field(description="Recommended next step for the support team")
