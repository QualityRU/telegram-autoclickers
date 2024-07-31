import asyncio
import random
import time

from config import AccountList, AccountsRecheckTime, MaxRandomDelay
from core.hamtercombat import HamsterKombatAccount
from core.logger import log


def RunAccounts():
    accounts = []
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
                f'AccountsRecheckTime and MaxRandomDelay values are set to 0, bot will close now.'
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
        asyncio.run(RunAccounts())
    except KeyboardInterrupt:
        log.error('Stopping Master Hamster Kombat Auto farming bot...')


if __name__ == '__main__':
    main()
