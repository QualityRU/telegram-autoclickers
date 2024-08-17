import os
import subprocess
import sys
import time

REPO_PATH = '.'
RESTART_DELAY = 2
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
        # Выполняем git pull для загрузки обновлений
        subprocess.run(['git', 'pull'], cwd=REPO_PATH, check=True)
        return True
    except Exception as e:
        print(f'Error pulling latest changes: {e}')
        return False


def restart_program():
    try:
        print('Restarting program...')
        time.sleep(RESTART_DELAY)
        python = sys.executable
        os.execl(python, python, MAIN_FILE, *sys.argv[1:])
    except Exception as e:
        print(f'Error restarting program: {e}')


def update_check():
    if get_git_status():
        print('New version available. Pulling latest changes...')
        if pull_latest_changes():
            print('Update downloaded. Restarting program...')
            restart_program()
        else:
            print('Failed to pull latest changes.')
    else:
        print('No updates available.')


if __name__ == '__main__':
    update_check()
