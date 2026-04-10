from pydantic import BaseModel, Field


class Action(BaseModel):
    action_type: int = Field(ge=0, le=4)