#!/bin/bash
# Doppelklick startet bskitool (Mac). Terminal offen lassen, solange du arbeitest.
cd "$(dirname "$0")" || exit 1
if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 fehlt. Bitte Python von https://www.python.org installieren."; read -r _; exit 1
fi
python3 bskitool.py ui
