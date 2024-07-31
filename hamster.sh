#!/bin/bash
screen -LRR -dmS hamster -c /etc/screenrc venv/bin/python3 hamster_combat/main.py
echo "Hamster запущен в фоне!"