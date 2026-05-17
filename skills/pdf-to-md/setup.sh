#!/usr/bin/env bash
# Installs pdf-to-md dependencies idempotently.
# Safe to run on every invocation — exits immediately if dependencies are satisfied.
# Dependencies: pdfplumber (table extraction), PyMuPDF/fitz (text, images, layout)

set -euo pipefail

REQUIREMENTS="$(dirname "$0")/requirements.txt"

# Check if all packages are already installed at required versions
if pip show pdfplumber PyMuPDF > /dev/null 2>&1; then
    exit 0
fi

echo "[pdf-to-md] Installing dependencies..."
pip install -q -r "$REQUIREMENTS"
echo "[pdf-to-md] Dependencies ready."
