#!/bin/bash
screen -LRR -dmS blum -c /etc/screenrc venv/bin/python3 blum/main.py
echo "Blum запущен в фоне!"