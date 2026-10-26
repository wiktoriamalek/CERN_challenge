# CERN PLC Simulator Challenge

An asynchronous PLC simulator that exposes its interface over OPC UA. The project uses `asyncua` and includes a pytest test suite.

## Requirements

- Python 3.11
- Poetry 2.x

## Install and run

```bash
cd "CERN challenge"
poetry env use 3.11
poetry install
poetry run python main.py
```

Run the tests from the same directory with `poetry run pytest`.
