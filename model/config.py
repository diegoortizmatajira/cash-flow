from datetime import date

from pydantic import BaseModel, field_validator


class Config(BaseModel):
    concept: str
    reference_date: date | None = None
    recurrence_in_days: int | None = None
    day_of_the_month: int | None = None
    checking_movement: float | None = None
    savings_movement: float | None = None
    credit_card_movement: float | None = None

    @field_validator("reference_date", mode="before")
    @classmethod
    def empty_str_to_none(cls, v: object) -> object:
        if v == "":
            return None
        return v
