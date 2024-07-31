#!/bin/bash
screen -LRR -dmS okx -c /etc/screenrc venv/bin/python3 okx_racer/main.py
echo "Okx Racer запущен в фоне!"