# PLC Simulator Project

Make sure `poetry` (https://python-poetry.org/) and `python@3.11` are installed on your system.

Run
```bash
poetry env use 3.11 
poetry install
```

Then run
```bash
poetry run python3 main.py &
```
Finally, run tests with 
```
poetry run pytest
```

Alarm tests don't work due to limited time and problems with race conditions on the OPC UA instance.