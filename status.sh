#!/usr/bin/env bash
status_path=$(cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd - P)
cd "$status_path"
MYPYPATH="$MYPYPATH:$status_path"
clear
echo "mypy:"
uvx mypy ./*.py ./t/end_to_end/*.py
echo ""
echo "ruff check:" 
uvx ruff check **.py
echo ""
echo "unit tests:"
grep --color=always -Irni "TODO" *.py
grep --color=always -Irni "FIXME" *.py
uv run -m unittest discover -s t/end_to_end -v
