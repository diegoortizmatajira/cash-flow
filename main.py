"""
Generate projected cash-flow movements for a given month based on a JSON configuration.
"""

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
    """
    Parse command-line arguments to determine the target year and month.

    Returns:
        argparse.Namespace: Parsed arguments containing 'year' and 'month'.
    """
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
    """
    Read the configuration file and validate its structure.

    Args:
        path (Path): The path to the configuration file. Defaults to CONFIG_PATH.

    Returns:
        list[Config]: A list of validated Config objects.
    """
    with open(path, "r", encoding="utf-8") as f:
        data: list[dict[str, object]] = json.load(f)
    adapter: TypeAdapter[list[Config]] = TypeAdapter(list[Config])
    return adapter.validate_python(data)


def generate_movements(configs: list[Config], year: int, month: int) -> list[Movement]:
    """
    Generate a list of movements for a given month based on the provided configuration.

    This function creates a list of financial movements using the provided configurations
    and a specified year and month. Depending on the configuration, movements can either:
    - Occur on a specific day of the month, or
    - Repeat at a regular interval starting from a reference date.

    Args:
        configs (list[Config]): A list of Config objects defining movement specifications.
        year (int): The target year for the movements.
        month (int): The target month for the movements.

    Returns:
        list[Movement]: A list of Movement objects sorted by date.
    """
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


def pretty_print_movements(movements: list[Movement]) -> None:
    """
    Display a list of financial movements in a readable tabular format.

    This function takes a list of Movement objects and prints them in a well-
    formatted table. Each attribute of the Movement model is displayed as a 
    column, with headers automatically derived from the model's fields. 

    Args:
        movements (list[Movement]): A list of Movement objects to be printed.

    Returns:
        None
    """
    if not movements:
        return
    fields: list[str] = list(Movement.model_fields.keys())
    rows: list[list[str]] = []
    for movement in movements:
        rows.append([str(getattr(movement, f) or "") for f in fields])
    col_widths: list[int] = [
        max(len(h), *(len(row[i]) for row in rows)) for i, h in enumerate(fields)
    ]
    header: str = "  ".join(h.ljust(w) for h, w in zip(fields, col_widths))
    separator: str = "  ".join("-" * w for w in col_widths)
    print(separator)
    print(header)
    print(separator)
    for row in rows:
        print("  ".join(v.ljust(w) for v, w in zip(row, col_widths)))


def print_movements_tsv(movements: list[Movement]) -> None:
    """
    Print a list of financial movements in TSV (Tab-Separated Values) format.

    This function takes a list of Movement objects and outputs them in a tab-separated format,
    suitable for copying into a spreadsheet for further analysis. The model's field names
    are used as column headers.

    Args:
        movements (list[Movement]): A list of Movement objects to be printed.

    Returns:
        None
    """
    if not movements:
        return
    fields: list[str] = list(Movement.model_fields.keys())
    print("\t".join(fields))
    for movement in movements:
        values: list[str] = [str(getattr(movement, f) or "") for f in fields]
        print("\t".join(values))


def main() -> None:
    """
    The main function of the script, orchestrating the cash-flow projection process.

    This function sets up logging, parses command-line arguments for the
    target year and month, reads configurations from a JSON file, generates
    financial movements based on the configurations, and displays the results
    in both a readable table format and TSV format for further analysis.

    Returns:
        None
    """
    logging.basicConfig(level=logging.WARNING)
    args: argparse.Namespace = parse_args()
    configs: list[Config] = read_config()
    movements: list[Movement] = generate_movements(configs, args.year, args.month)
    pretty_print_movements(movements)
    print()
    print("--- TSV (copy and paste into a spreadsheet) ---")
    print()
    print_movements_tsv(movements)


if __name__ == "__main__":
    main()
