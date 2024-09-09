import asyncio
import os
import random
import sys
import time
import traceback

from core.api import (
    AccountList,
    AccountsRecheckTime,
    HamsterKombatAccount,
    MaxRandomDelay,
    clear_screen,
    log,
    w,
)

accounts = []


def RunAccounts():
    for account in AccountList:
        accounts.append(HamsterKombatAccount(account))
        accounts[-1].SendTelegramLog(
            f'[{accounts[-1].account_name}] Hamster Kombat Auto farming bot started successfully.',
            'general_info',
        )

    while True:
        print(
            f' {w.y}===============[ STARTING ALL ACCOUNTS ]=============== {w.rs}'
        )
        for account in accounts:
            account.Start()

        if AccountsRecheckTime < 1 and MaxRandomDelay < 1:
            log.error(
                f'{w.r}AccountsRecheckTime{w.rs} and {w.r}MaxRandomDelay{w.rs} values are set to 0, bot will close now.'
            )
            return

        if MaxRandomDelay > 0:
            randomDelay = random.randint(1, MaxRandomDelay)
            log.error(
                f' 😴 Sleeping for {randomDelay} seconds because of random delay.'
            )
            time.sleep(randomDelay)

        if AccountsRecheckTime > 0:
            log.warning(
                f' 💤 Rechecking all accounts in {AccountsRecheckTime} seconds.'
            )
            time.sleep(AccountsRecheckTime)


def loading_bar2(duration):
    total_steps = 20
    interval = duration / total_steps

    print('Loading:', end=' ', flush=True)

    for i in range(1, total_steps + 1):
        sys.stdout.write(
            f"\rLoading: {'█' * i}{' ' * (total_steps - i)} {int(i * 100 / total_steps)}%"
        )
        sys.stdout.flush()
        time.sleep(interval)

    sys.stdout.write(f"\rLoading: {'█' * total_steps} 100%\n")
    sys.stdout.flush()


def main():
    clear_screen()
    loading_bar2(5)
    clear_screen()

    try:
        asyncio.run(RunAccounts())
    except KeyboardInterrupt:
        log.error('Bot Stop by user!')
    except Exception as e:
        accounts[0].SendTelegramLog(
            f'[{accounts[0].account_name}] Main error.\n\n{traceback.format_exc()}',
            'other_errors',
        )


if __name__ == '__main__':
    main()
