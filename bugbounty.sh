#!/bin/bash
# BugBountyTool - Linux/Mac launcher
# Uso: ./bugbounty.sh dominio.com

cd "$(dirname "$0")/src"
python main.py "$@"