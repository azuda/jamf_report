#!/bin/sh

PROJECT="$PWD"
VENV="$PROJECT/.venv/bin/python3"

echo "Script start @ $(date)"

$VENV query_jamf.py
$VENV computer_report.py
$VENV device_report.py
$VENV upload.py

echo "\nScript end @ $(date)"
