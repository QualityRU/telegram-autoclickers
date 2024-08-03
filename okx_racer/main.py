from colorama import Fore
from core.api import OKXAcount

if __name__ == '__main__':
    okx = OKXAcount()
    try:
        okx.main()
    except Exception as e:
        print(Fore.RED + str(e))
        exit(1)
