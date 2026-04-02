from datetime import date
from pydantic import BaseModel


class Movement(BaseModel):
    date: date
    concept: str
    checking_movement: float | None = None
    credit_card_movement: float | None = None
    savings_movement: float | None = None
