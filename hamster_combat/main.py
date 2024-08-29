import asyncio
import random
import time
import traceback

from core.api import HamsterKombatAccount, log

# from updater import start_update_checker

# start_update_checker()

try:
    from config import (
        AccountList,
        AccountsRecheckTime,
        ConfigFileVersion,
        MaxRandomDelay,
    )
except ImportError:
    print('Config file not found.')
    print('Create a copy of config.py.example and rename it to config.py')
    print('And fill in the required fields.')
    exit()

if 'ConfigFileVersion' not in locals() or ConfigFileVersion != 1:
    print('Invalid config file version.')
    print('Please update the config file to the latest version.')
    print('Create a copy of config.py.example and rename it to config.py')
    print('And fill in the required fields.')
    exit()

accounts = []


def RunAccounts(accounts):
    for account in AccountList:
        accounts.append(HamsterKombatAccount(account))
        accounts[-1].SendTelegramLog(
            f'[{accounts[-1].account_name}] Hamster Kombat Auto farming bot started successfully.',
            'general_info',
        )

    while True:
        log.info('\033[1;33mStarting all accounts...\033[0m')
        for account in accounts:
            account.Start()

        if AccountsRecheckTime < 1 and MaxRandomDelay < 1:
            log.error(
                'AccountsRecheckTime and MaxRandomDelay values are set to 0, bot will close now.'
            )
            return

        if MaxRandomDelay > 0:
            randomDelay = random.randint(1, MaxRandomDelay)
            log.error(
                f'Sleeping for {randomDelay} seconds because of random delay...'
            )
            time.sleep(randomDelay)

        if AccountsRecheckTime > 0:
            log.error(
                f'Rechecking all accounts in {AccountsRecheckTime} seconds...'
            )
            time.sleep(AccountsRecheckTime)


def main():
    log.info(
        '------------------------------------------------------------------------'
    )
    log.info(
        '------------------------------------------------------------------------'
    )
    log.info(
        '\033[1;32mWelcome to [Master Hamster Kombat] Auto farming bot...\033[0m'
    )
    log.info('\033[1;36mTo stop the bot, press Ctrl + C\033[0m')
    log.info(
        '------------------------------------------------------------------------'
    )
    log.info(
        '------------------------------------------------------------------------'
    )

    time.sleep(2)
    try:
        asyncio.run(RunAccounts(accounts))
    except KeyboardInterrupt:
        log.error('Stopping Master Hamster Kombat Auto farming bot...')
    except Exception as e:
        accounts[0].SendTelegramLog(
            f'[{accounts[0].account_name}] Main error.\n\n{traceback.format_exc()}',
            'other_errors',
        )


if __name__ == '__main__':
    main()
