import os
import subprocess
import sys
import threading
import time

import schedule

REPO_PATH = '.'
RESTART_DELAY = 2
CHECK_INTERVAL = 2
MAIN_FILE = 'main.py'


def get_git_status():
    try:
        subprocess.run(['git', 'fetch'], cwd=REPO_PATH, check=True)
        result = subprocess.run(
            ['git', 'status', '-uno'],
            cwd=REPO_PATH,
            capture_output=True,
            text=True,
        )
        return 'behind' in result.stdout
    except Exception as e:
        print(f'Error checking Git status: {e}')
        return False


def pull_latest_changes():
    try:
        subprocess.run(['git', 'pull'], cwd=REPO_PATH, check=True)
        return True
    except Exception as e:
        print(f'Error pulling latest changes: {e}')
        return False


def restart_program():
    try:
        print('Restarting main.py...')
        time.sleep(RESTART_DELAY)
        python = sys.executable
        os.execl(python, python, MAIN_FILE)
    except Exception as e:
        print(f'Error restarting main.py: {e}')


def update_check():
    if get_git_status():
        print('New version available. Pulling latest changes...')
        if pull_latest_changes():
            print('Update downloaded. Restarting main.py...')
            restart_program()
        else:
            print('Failed to pull latest changes.')


def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)


def start_update_checker():
    schedule.every(CHECK_INTERVAL).seconds.do(update_check)
    schedule_thread = threading.Thread(target=run_schedule)
    schedule_thread.daemon = True
    schedule_thread.start()
