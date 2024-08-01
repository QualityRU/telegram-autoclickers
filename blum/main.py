from os import system as sys
from platform import system as s_name
from threading import Thread

from colorama import Fore
from config import ACCOUNTS
from core.blum import BlumAccount


def main():
    sys('cls') if s_name() == 'Windows' else sys('clear')

    def Start_Thread(Account, URL, Proxy=None):
        Blum = BlumAccount(Account, URL, Proxy)
        Blum.Run()

    try:
        for Account, URL in ACCOUNTS.items():
            Thread(
                target=Start_Thread,
                args=(
                    Account,
                    URL,
                ),
            ).start()
    except Exception:
        print(
            Fore.RED
            + '\n\tОшибка чтения ACCOUNTS, ссылки указаны некорректно!'
        )


if __name__ == '__main__':
    main()
