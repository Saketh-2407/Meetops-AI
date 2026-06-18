from typing import Dict, Literal

from pydantic import BaseModel


class ApprovalRequest(BaseModel):
    # Maps an action_id to the user's decision.
    decisions: Dict[str, Literal["approved", "rejected"]]
