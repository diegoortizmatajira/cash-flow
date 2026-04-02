import argparse
import json
import logging
from calendar import monthrange
from datetime import date, timedelta
from pathlib import Path

from pydantic import TypeAdapter

from model.config import Config
from model.movement import Movement

CONFIG_PATH: Path = Path("./data/config.json")

logger: logging.Logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Generate projected cash-flow movements for a given month.",
    )
    parser.add_argument(
        "year",
        type=int,
        help="Target year (e.g. 2026)",
    )
    parser.add_argument(
        "month",
        type=int,
        choices=range(1, 13),
        metavar="month",
        help="Target month (1–12)",
    )
    return parser.parse_args()


def read_config(path: Path = CONFIG_PATH) -> list[Config]:
    with open(path, "r", encoding="utf-8") as f:
        data: list[dict[str, object]] = json.load(f)
    adapter: TypeAdapter[list[Config]] = TypeAdapter(list[Config])
    return adapter.validate_python(data)


def generate_movements(configs: list[Config], year: int, month: int) -> list[Movement]:
    movements: list[Movement] = []
    first_day: date = date(year, month, 1)
    last_day_number: int = monthrange(year, month)[1]
    last_day: date = date(year, month, last_day_number)

    for config in configs:
        if config.day_of_the_month is not None:
            day: int = min(config.day_of_the_month, last_day_number)
            movements.append(
                Movement(
                    date=date(year, month, day),
                    concept=config.concept,
                    checking_movement=config.checking_movement,
                    savings_movement=config.savings_movement,
                    credit_card_movement=config.credit_card_movement,
                )
            )
        elif (
            config.reference_date is not None and config.recurrence_in_days is not None
        ):
            days_from_ref: int = (first_day - config.reference_date).days
            remainder: int = days_from_ref % config.recurrence_in_days
            if remainder <= 0:
                first_occurrence: date = first_day
            else:
                first_occurrence = first_day + timedelta(
                    days=config.recurrence_in_days - remainder
                )
            current: date = first_occurrence
            while current <= last_day:
                movements.append(
                    Movement(
                        date=current,
                        concept=config.concept,
                        checking_movement=config.checking_movement,
                        savings_movement=config.savings_movement,
                        credit_card_movement=config.credit_card_movement,
                    )
                )
                current = current + timedelta(days=config.recurrence_in_days)
        else:
            logger.warning(
                "Config '%s' has neither day_of_the_month nor "
                "reference_date/recurrence_in_days — skipping.",
                config.concept,
            )

    movements.sort(key=lambda m: m.date)
    return movements


def print_movements(movements: list[Movement]) -> None:
    if not movements:
        return
    fields: list[str] = list(Movement.model_fields.keys())
    print("\t".join(fields))
    for movement in movements:
        values: list[str] = [str(getattr(movement, f) or "") for f in fields]
        print("\t".join(values))


def main() -> None:
    logging.basicConfig(level=logging.WARNING)
    args: argparse.Namespace = parse_args()
    configs: list[Config] = read_config()
    movements: list[Movement] = generate_movements(configs, args.year, args.month)
    print_movements(movements)


if __name__ == "__main__":
    main()
