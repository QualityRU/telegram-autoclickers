from datetime import datetime, timedelta
from random import randint
from time import sleep
from typing import Literal
from urllib.parse import unquote

from colorama import Fore
from core.tread_lock import Console_Lock
from requests import get, post

from .settings import COINS, HEADERS


class BlumAccount:
    def __init__(self, Name: str, URL: str, Proxy: dict) -> None:
        self.Name = Name
        self.URL = self.URL_Clean(URL)
        self.Proxy = Proxy
        self.Token = self.Authentication()

    def URL_Clean(self, URL: str) -> str:
        """Очистка уникальной ссылки от лишних элементов"""

        try:
            return unquote(
                URL.split('#tgWebAppData=')[1].split('&tgWebAppVersion')[0]
            )
        except:
            return ''

    def Current_Time(self) -> str:
        """Текущее время"""

        return Fore.BLUE + f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'

    def Logging(
        self,
        Type: Literal['Success', 'Warning', 'Error'],
        Name: str,
        Smile: str,
        Text: str,
    ) -> None:
        """Логирование"""

        with Console_Lock:
            COLOR = (
                Fore.GREEN
                if Type == 'Success'
                else Fore.YELLOW
                if Type == 'Warning'
                else Fore.RED
            )   # Цвет текста
            DIVIDER = Fore.BLACK + ' | '   # Разделитель

            Time = self.Current_Time()     # Текущее время
            Name = Fore.MAGENTA + Name     # Ник аккаунта
            Smile = COLOR + str(Smile)     # Смайлик
            Text = COLOR + Text            # Текст лога

            print(Time + DIVIDER + Smile + DIVIDER + Text + DIVIDER + Name)

    def Authentication(self) -> str:
        """Аутентификация аккаунта"""

        URL = 'https://user-domain.blum.codes/api/v1/auth/provider/PROVIDER_TELEGRAM_MINI_APP'
        Json = {'query': self.URL}

        try:
            Token = post(
                URL, headers=HEADERS, json=Json, proxies=self.Proxy
            ).json()['token']['access']
            self.Logging('Success', self.Name, '🟢', 'Инициализация успешна!')
            return Token
        except Exception:
            self.Logging('Error', self.Name, '🔴', 'Ошибка инициализации!')
            return ''

    def ReAuthentication(self) -> None:
        """Повторная аутентификация аккаунта"""

        self.Token = self.Authentication()

    def Get_Info(self) -> dict:
        """Получение информации о балансе и наличии доступных игр"""

        URL = 'https://game-domain.blum.codes/api/v1/user/balance'
        Headers_bear = HEADERS.copy()
        Headers_bear['authorization'] = f'Bearer {self.Token}'

        try:
            res = get(URL, headers=Headers_bear, proxies=self.Proxy).json()

            Balance = res['availableBalance']   # Текущий баланс
            Plays = res['playPasses']   # Доступное кол-во игр

            return {'Balance': f'{float(Balance):,.0f}', 'Plays': Plays}
        except Exception:
            return None

    def Get_Time_Now(self) -> dict:
        """Получение времени"""

        URL = 'https://game-domain.blum.codes/api/v1/time/now'
        Headers_bear = HEADERS.copy()
        Headers_bear['authorization'] = f'Bearer {self.Token}'

        try:
            return get(URL, headers=Headers_bear, proxies=self.Proxy).json()
        except Exception:
            return None

    def Daily_Reward(self) -> bool:
        """Получение ежедневной награды"""

        URL = 'https://game-domain.blum.codes/api/v1/daily-reward?offset=-600'
        Headers_bear = HEADERS.copy()
        Headers_bear['authorization'] = f'Bearer {self.Token}'

        try:
            res = post(URL, headers=Headers_bear, proxies=self.Proxy)

            if res.text == 'OK':
                return True
            else:
                return False
        except Exception:
            return False

    def Claim(self) -> None:
        """Сбор монет"""

        URL = 'https://game-domain.blum.codes/api/v1/farming/claim'
        Headers_bear = HEADERS.copy()
        Headers_bear['authorization'] = f'Bearer {self.Token}'

        try:
            post(URL, headers=Headers_bear, proxies=self.Proxy).json()[
                'availableBalance'
            ]
            self.Logging('Success', self.Name, '🟢', 'Монеты собраны!')
        except Exception:
            self.Logging('Error', self.Name, '🔴', 'Монеты не собраны!')

    def Start_Farm(self) -> None:
        """Запуск фарма монет"""

        URL = 'https://game-domain.blum.codes/api/v1/farming/start'
        Headers_bear = HEADERS.copy()
        Headers_bear['authorization'] = f'Bearer {self.Token}'

        try:
            post(URL, headers=Headers_bear, proxies=self.Proxy).json()[
                'startTime'
            ]
            self.Logging('Success', self.Name, '🟢', 'Фарм монет запущен!')
        except Exception:
            self.Logging('Error', self.Name, '🔴', 'Фарм монет не запущен!')

    def Referal_Claim(self) -> bool:
        """Сбор монет за рефералов"""

        URL = 'https://gateway.blum.codes/v1/friends/claim'
        Headers_bear = HEADERS.copy()
        Headers_bear['authorization'] = f'Bearer {self.Token}'

        try:
            post(URL, headers=Headers_bear, proxies=self.Proxy).json()[
                'claimBalance'
            ]
            return True
        except Exception:
            return False

    def Play(self) -> None:
        """Запуск игры"""

        URL_1 = 'https://game-domain.blum.codes/api/v2/game/play'
        URL_2 = 'https://game-domain.blum.codes/api/v2/game/claim'
        Headers_1_bear = HEADERS.copy()
        Headers_1_bear['authorization'] = f'Bearer {self.Token}'

        Headers_2_bear = HEADERS.copy()
        Headers_2_bear['authorization'] = f'Bearer {self.Token}'

        try:
            GID = post(
                URL_1, headers=Headers_1_bear, proxies=self.Proxy
            ).json()[
                'gameId'
            ]   # Запуск и получение ID игры
            _COINS = randint(
                COINS[0], COINS[1]
            )   # Желаемое кол-во получения монет
            sleep(30)   # Ожидание 30 секунд, для показа реальности игры

            post(
                URL_2,
                headers=Headers_2_bear,
                json={'gameId': str(GID), 'points': _COINS},
                proxies=self.Proxy,
            )
            self.Logging(
                'Success', self.Name, '🟢', f'Игра сыграна! +{_COINS}!'
            )
        except Exception:
            self.Logging('Error', self.Name, '🔴', 'Игра не сыграна!')

    def Get_Tasks(self) -> list:
        """Список заданий"""

        URL = 'https://earn-domain.blum.codes/api/v1/tasks'
        Headers_bear = HEADERS.copy()
        Headers_bear['authorization'] = f'Bearer {self.Token}'

        try:
            return get(URL, headers=Headers_bear, proxies=self.Proxy).json()
        except Exception:
            return []

    def Start_Tasks(self, ID: str) -> bool:
        """Запуск задания"""

        URL = f'https://earn-domain.blum.codes/api/v1/tasks/{ID}/start'
        Headers_bear = HEADERS.copy()
        Headers_bear['authorization'] = f'Bearer {self.Token}'

        try:
            return (
                True
                if post(URL, headers=Headers_bear, proxies=self.Proxy).json()[
                    'STARTED'
                ]
                else False
            )
        except Exception:
            return False

    def Claim_Tasks(self, ID: str) -> dict:
        """Получение награды за выполненное задание"""

        URL = f'https://earn-domain.blum.codes/api/v1/tasks/{ID}/claim'
        Headers_bear = HEADERS.copy()
        Headers_bear['authorization'] = f'Bearer {self.Token}'

        try:
            res = post(URL, headers=Headers_bear, proxies=self.Proxy).json()

            Status = res['status']   # Статус задания
            Reward = res['reward']   # Награда

            if Status == 'FINISHED':
                return {'Status': True, 'Reward': Reward}
            else:
                return {'Status': False}
        except Exception:
            return {'Status': False}

    def Run(self) -> None:
        """Активация бота"""

        while True:
            try:
                if self.Token:   # Если аутентификация успешна
                    self.Logging(
                        'Success',
                        self.Name,
                        '💰',
                        f'Текущий баланс: {self.Get_Info()["Balance"]}',
                    )

                    if self.Daily_Reward():   # Получение ежедневной награды
                        self.Logging(
                            'Success',
                            self.Name,
                            '🟢',
                            'Ежедневная награда получена!',
                        )
                        sleep(randint(3, 6))   # Промежуточное ожидание

                    if self.Get_Time_Now():
                        self.Logging(
                            'Success', self.Name, '🟢', 'Время получено!'
                        )

                    self.Claim()   # Сбор монет
                    sleep(randint(3, 6))   # Промежуточное ожидание
                    self.Start_Farm()   # Запуск фарма монет
                    sleep(randint(3, 6))   # Промежуточное ожидание

                    if self.Referal_Claim():   # Сбор монет за рефералов
                        self.Logging(
                            'Success',
                            self.Name,
                            '🟢',
                            'Монеты за рефералов собраны!',
                        )
                        sleep(randint(3, 6))   # Промежуточное ожидание

                    # Получение кол-ва доступных игр и запуск их прохождения
                    Get_plays = self.Get_Info()['Plays']
                    if Get_plays > 0:
                        self.Logging(
                            'Success',
                            self.Name,
                            '🎮',
                            f'Игр доступно: {Get_plays}!',
                        )
                        for _ in range(Get_plays):
                            self.Play()
                            sleep(randint(3, 6))

                        self.Logging(
                            'Success',
                            self.Name,
                            '💰',
                            f'Баланс после игр: {self.Get_Info()["Balance"]}',
                        )

                    # Выполнение всех доступных заданий
                    started = 0
                    completed = 0
                    Category = self.Get_Tasks()   # Список заданий
                    for Section in Category:
                        tasks = Section.get('tasks', [])
                        for task in tasks:
                            if started == 2 or completed == 2:
                                break
                            if task['status'] == 'FINISHED' or task.get(
                                'isHidden', False
                            ):
                                continue
                            if 'socialSubscription' not in task or task.get(
                                'socialSubscription', {}
                            ).get('openInTelegram', False):
                                continue
                            if task['status'] == 'NOT_STARTED':
                                self.Start_Tasks(task['id'])
                                sleep(randint(3, 6))
                                started += 1
                            elif task['status'] == 'READY_FOR_CLAIM':
                                if self.Claim_Tasks(task['id']):
                                    self.Logging(
                                        'Success',
                                        self.Name,
                                        '⚡️',
                                        'Задание выполнено!',
                                    )
                                sleep(randint(3, 6))
                                completed += 1
                        sub_sections = Section.get('subSections', [])
                        for sub_section in sub_sections:
                            tasks = sub_section.get('tasks', [])
                            for task in tasks:
                                if started == 2 or completed == 2:
                                    break
                                if task['status'] == 'FINISHED' or task.get(
                                    'isHidden', False
                                ):
                                    continue
                                if (
                                    'socialSubscription' not in task
                                    or task.get('socialSubscription', {}).get(
                                        'openInTelegram', False
                                    )
                                ):
                                    continue
                                if task['status'] == 'NOT_STARTED':
                                    self.Start_Tasks(task['id'])
                                    sleep(randint(3, 6))
                                    started += 1
                                elif task['status'] == 'READY_FOR_CLAIM':
                                    if self.Claim_Tasks(task['id']):
                                        self.Logging(
                                            'Success',
                                            self.Name,
                                            '⚡️',
                                            'Задание выполнено!',
                                        )
                                    sleep(randint(3, 6))
                                    completed += 1
                    Waiting = randint(
                        3_500, 3_600
                    )   # Значение времени в секундах для ожидания
                    Waiting_STR = (
                        datetime.now() + timedelta(seconds=Waiting)
                    ).strftime(
                        '%Y-%m-%d %H:%M:%S'
                    )   # Значение времени в читаемом виде

                    self.Logging(
                        'Success',
                        self.Name,
                        '💰',
                        f'Текущий баланс: {self.Get_Info()["Balance"]}',
                    )
                    self.Logging(
                        'Warning',
                        self.Name,
                        '⏳',
                        f'Следующий сбор: {Waiting_STR}!',
                    )

                    sleep(Waiting)   # Ожидание от 8 до 9 часов
                    self.ReAuthentication()   # Повторная аутентификация аккаунта

                else:   # Если аутентификация не успешна
                    sleep(randint(33, 66))   # Ожидание от 33 до 66 секунд
                    self.ReAuthentication()   # Повторная аутентификация аккаунта
            except Exception:
                pass
