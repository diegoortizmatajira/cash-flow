# Cash Flow

A command-line tool that generates projected cash-flow movements for a given
month based on recurring financial entries you define in a configuration file.

## Requirements

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) (recommended for dependency management)

## Installation

```bash
uv sync
```

## Configuration

The app reads its configuration from `data/config.json`. A sample file is
provided at `data/config.sample.json` — copy and rename it to get started:

```bash
cp data/config.sample.json data/config.json
```

Then edit `data/config.json` with your own financial entries. The file is
git-ignored so your personal data stays private.

### Configuration format

The configuration file is a JSON array of entries. Each entry represents a
recurring financial movement and supports two scheduling modes:

#### Fixed day of the month

Use `day_of_the_month` to schedule a movement on the same calendar day every
month. If the month has fewer days, it falls on the last day.

```json
{
  "concept": "Payment for home internet",
  "day_of_the_month": 5,
  "checking_movement": -80
}
```

#### Recurring from a reference date

Use `reference_date` and `recurrence_in_days` to schedule movements that repeat
every N days starting from a known date (e.g. biweekly paychecks).

```json
{
  "concept": "Income from work",
  "reference_date": "2026-02-09",
  "recurrence_in_days": 14,
  "checking_movement": 1500
}
```

### Entry fields

| Field                  | Type   | Required | Description                        |
| ---------------------- | ------ | -------- | ---------------------------------- |
| `concept`              | string | Yes      | Description of the movement        |
| `day_of_the_month`     | int    | No       | Fixed calendar day (1-31)          |
| `reference_date`       | string | No       | Start date in `YYYY-MM-DD` format  |
| `recurrence_in_days`   | int    | No       | Recurrence interval in days        |
| `checking_movement`    | float  | No       | Amount applied to checking account |
| `savings_movement`     | float  | No       | Amount applied to savings account  |
| `credit_card_movement` | float  | No       | Amount applied to credit card      |

Each entry must have either `day_of_the_month` **or** both `reference_date` and
`recurrence_in_days`. Entries missing both are skipped with a warning. Use
positive values for income and negative values for expenses.

### Transfers between accounts

A transfer between accounts can be represented with a single entry by setting a
negative value on the source account and a positive value on the destination
account. For example, to move $500 from checking to savings on the 1st of every
month:

```json
{
  "concept": "Monthly savings transfer",
  "day_of_the_month": 1,
  "checking_movement": -500,
  "savings_movement": 500
}
```

Similarly, to pay off a credit card balance from checking:

```json
{
  "concept": "Credit card payment",
  "day_of_the_month": 15,
  "checking_movement": -1200,
  "credit_card_movement": 1200
}
```

Because the amounts offset each other, the net effect across all accounts is
zero — exactly what a transfer should be.

## Usage

```bash
uv run cash-flow <year> <month>
```

For example, to generate projected movements for March 2026:

```bash
uv run cash-flow 2026 3
```

The output is printed as tab-separated values with the columns: `date`,
`concept`, `checking_movement`, `credit_card_movement`, and `savings_movement`.
