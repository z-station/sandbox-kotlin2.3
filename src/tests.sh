#!/bin/bash
PYTHONPATH=. poetry run pytest -vv -p no:cacheprovider
