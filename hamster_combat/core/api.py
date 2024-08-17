import base64
import datetime
import json
import random
import time
import uuid

import requests
from config import (
    AccountList,
    AccountsRecheckTime,
    MaxRandomDelay,
    telegramBotLogging,
)
from core.logger import log
from core.promogames import SupportedPromoGames
from core.utilities import (
    CalculateCardProfitCoefficient,
    DailyCipherDecode,
    SortUpgrades,
    TextToMorseCode,
    number_to_string,
)


class HamsterKombatAccount:
    def __init__(self, AccountData):
        self.account_name = AccountData['account_name']
        self.Authorization = AccountData['Authorization']
        self.UserAgent = AccountData['UserAgent']
        self.Config_Version = None
        self.Proxy = AccountData['Proxy']
        self.config = AccountData['config']
        self.isAndroidDevice = 'Android' in self.UserAgent
        self.balanceCoins = 0
        self.availableTaps = 0
        self.maxTaps = 0
        self.ProfitPerHour = 0
        self.earnPassivePerHour = 0
        self.SpendTokens = 0
        self.account_data = None
        self.telegram_chat_id = AccountData['telegram_chat_id']
        self.totalKeys = 0
        self.balanceKeys = 0
        self.availableSkins = {}
        self.level = 0

    def GetConfig(self, key, default=None):
        if key in self.config:
            return self.config[key]
        return default

    def SendTelegramLog(self, message, level='other_errors'):
        if (
            not telegramBotLogging['is_active']
            or self.telegram_chat_id == ''
            or telegramBotLogging['bot_token'] == ''
        ):
            return

        if (
            level not in telegramBotLogging['messages']
            or telegramBotLogging['messages'][level] is False
        ):
            return

        try:
            requests.get(
                f"https://api.telegram.org/bot{telegramBotLogging['bot_token']}/sendMessage?chat_id={self.telegram_chat_id}&text={message}"
            )
        except Exception as e:
            log.error(f'[{self.account_name}] TelegramLog error: {e}')

    # Send HTTP requests
    def HttpRequest(
        self,
        url,
        headers,
        method='POST',
        validStatusCodes=200,
        payload=None,
        ignore_errors=False,
    ):
        # Default headers
        defaultHeaders = {
            'Accept': '*/*',
            'Connection': 'keep-alive',
            'Host': 'api.hamsterkombatgame.io',
            'Origin': 'https://hamsterkombatgame.io',
            'Referer': 'https://hamsterkombatgame.io/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'User-Agent': self.UserAgent,
        }

        # Add default headers for Android devices to avoid detection, Not needed for iOS devices
        if self.isAndroidDevice:
            defaultHeaders['HTTP_SEC_CH_UA_PLATFORM'] = '"Android"'
            defaultHeaders['HTTP_SEC_CH_UA_MOBILE'] = '?1'
            defaultHeaders[
                'HTTP_SEC_CH_UA'
            ] = '"Android WebView";v="125", "Chromium";v="125", "Not.A/Brand";v="24"'
            defaultHeaders[
                'HTTP_X_REQUESTED_WITH'
            ] = 'org.telegram.messenger.web'

        # Add and replace new headers to default headers
        for key, value in headers.items():
            defaultHeaders[key] = value

        try:
            if method == 'GET':
                response = requests.get(
                    url, headers=defaultHeaders, proxies=self.Proxy
                )
            elif method == 'POST':
                response = requests.post(
                    url, headers=headers, data=payload, proxies=self.Proxy
                )
            elif method == 'OPTIONS':
                response = requests.options(
                    url, headers=headers, proxies=self.Proxy
                )
            else:
                log.error(f'[{self.account_name}] Invalid method: {method}')
                self.SendTelegramLog(
                    f'[{self.account_name}] Invalid method: {method}',
                    'http_errors',
                )
                return None

            if response.status_code != validStatusCodes:
                if ignore_errors:
                    return None

                log.error(
                    f'[{self.account_name}] Status code is not {validStatusCodes}'
                )
                log.error(f'[{self.account_name}] Response: {response.text}')
                self.SendTelegramLog(
                    f'[{self.account_name}] Status code is not {validStatusCodes}',
                    'http_errors',
                )
                return None

            if method == 'OPTIONS':
                return True

            if response.headers.get('config-version'):
                self.Config_Version = response.headers.get('config-version')
            return response.json()
        except Exception as e:
            if ignore_errors:
                return None
            log.error(f'[{self.account_name}] Error: {e}')
            self.SendTelegramLog(
                f'[{self.account_name}] Error: {e}', 'http_errors'
            )
            return None

    # Sending sync request
    def syncRequest(self):
        url = 'https://api.hamsterkombatgame.io/clicker/sync'
        headers = {
            'Access-Control-Request-Headers': self.Authorization,
            'Access-Control-Request-Method': 'POST',
        }

        # Send OPTIONS request
        self.HttpRequest(url, headers, 'OPTIONS', 204)

        headers = {
            'Authorization': self.Authorization,
        }

        # Send POST request
        return self.HttpRequest(url, headers, 'POST', 200)

    # Get list of upgrades to buy
    def UpgradesForBuyRequest(self):
        url = 'https://api.hamsterkombatgame.io/clicker/upgrades-for-buy'
        headers = {
            'Access-Control-Request-Headers': 'authorization',
            'Access-Control-Request-Method': 'POST',
        }

        # Send OPTIONS request
        self.HttpRequest(url, headers, 'OPTIONS', 204)

        headers = {
            'Authorization': self.Authorization,
        }

        # Send POST request
        return self.HttpRequest(url, headers, 'POST', 200)

    # Buy an upgrade
    def BuyUpgradeRequest(self, UpgradeId):
        url = 'https://api.hamsterkombatgame.io/clicker/buy-upgrade'
        headers = {
            'Access-Control-Request-Headers': 'authorization,content-type',
            'Access-Control-Request-Method': 'POST',
        }

        # Send OPTIONS request
        self.HttpRequest(url, headers, 'OPTIONS', 204)

        headers = {
            'Authorization': self.Authorization,
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }

        payload = json.dumps(
            {
                'upgradeId': UpgradeId,
                'timestamp': int(datetime.datetime.now().timestamp() * 1000),
            }
        )

        # Send POST request
        return self.HttpRequest(url, headers, 'POST', 200, payload)

    def ClaimDailyComboRequest(self):
        url = 'https://api.hamsterkombatgame.io/clicker/claim-daily-combo'
        headers = {
            'Access-Control-Request-Headers': 'authorization',
            'Access-Control-Request-Method': 'POST',
        }

        # Send OPTIONS request
        self.HttpRequest(url, headers, 'OPTIONS', 204)

        headers = {
            'Authorization': self.Authorization,
        }

        # Send POST request
        return self.HttpRequest(url, headers, 'POST', 200)

    # Tap the hamster
    def TapRequest(self, tap_count):
        url = 'https://api.hamsterkombatgame.io/clicker/tap'
        headers = {
            'Access-Control-Request-Headers': 'authorization,content-type',
            'Access-Control-Request-Method': 'POST',
        }

        # Send OPTIONS request
        self.HttpRequest(url, headers, 'OPTIONS', 204)

        headers = {
            'Accept': 'application/json',
            'Authorization': self.Authorization,
            'Content-Type': 'application/json',
        }

        payload = json.dumps(
            {
                'timestamp': int(datetime.datetime.now().timestamp() * 1000),
                'availableTaps': 0,
                'count': int(tap_count),
            }
        )

        # Send POST request
        return self.HttpRequest(url, headers, 'POST', 200, payload)

    # Get list of boosts to buy
    def BoostsToBuyListRequest(self):
        url = 'https://api.hamsterkombatgame.io/clicker/boosts-for-buy'
        headers = {
            'Access-Control-Request-Headers': 'authorization',
            'Access-Control-Request-Method': 'POST',
        }

        # Send OPTIONS request
        self.HttpRequest(url, headers, 'OPTIONS', 204)

        headers = {
            'Authorization': self.Authorization,
        }

        # Send POST request
        return self.HttpRequest(url, headers, 'POST', 200)

    # Buy a boost
    def BuyBoostRequest(self, boost_id):
        url = 'https://api.hamsterkombatgame.io/clicker/buy-boost'
        headers = {
            'Access-Control-Request-Headers': 'authorization,content-type',
            'Access-Control-Request-Method': 'POST',
        }

        # Send OPTIONS request
        self.HttpRequest(url, headers, 'OPTIONS', 204)

        headers = {
            'Accept': 'application/json',
            'Authorization': self.Authorization,
            'Content-Type': 'application/json',
        }

        payload = json.dumps(
            {
                'boostId': boost_id,
                'timestamp': int(datetime.datetime.now().timestamp() * 1000),
            }
        )

        # Send POST request
        return self.HttpRequest(url, headers, 'POST', 200, payload)

    def getAccountData(self):
        account_data = self.syncRequest()
        if account_data is None or account_data is False:
            log.error(f'[{self.account_name}] Unable to get account data.')
            self.SendTelegramLog(
                f'[{self.account_name}] Unable to get account data.',
                'other_errors',
            )
            return False

        if 'clickerUser' not in account_data:
            log.error(f'[{self.account_name}] Invalid account data.')
            self.SendTelegramLog(
                f'[{self.account_name}] Invalid account data.', 'other_errors'
            )
            return False

        if 'balanceCoins' not in account_data['clickerUser']:
            log.error(f'[{self.account_name}] Invalid balance coins.')
            self.SendTelegramLog(
                f'[{self.account_name}] Invalid balance coins.', 'other_errors'
            )
            return False

        self.account_data = account_data
        self.balanceCoins = account_data['clickerUser']['balanceCoins']
        self.availableTaps = account_data['clickerUser']['availableTaps']
        self.maxTaps = account_data['clickerUser']['maxTaps']
        self.earnPassivePerHour = account_data['clickerUser'][
            'earnPassivePerHour'
        ]
        self.availableSkins = account_data['clickerUser']['skin']
        self.level = account_data['clickerUser']['level']
        if 'balanceKeys' in account_data['clickerUser']:
            self.balanceKeys = account_data['clickerUser']['balanceKeys']
        else:
            self.balanceKeys = 0

        if 'totalKeys' in account_data['clickerUser']:
            self.totalKeys = account_data['clickerUser']['totalKeys']
        else:
            self.totalKeys = 0

        return account_data

    def BuyFreeTapBoostIfAvailable(self):
        log.info(f'[{self.account_name}] Checking for free tap boost...')

        BoostList = self.BoostsToBuyListRequest()
        if BoostList is None:
            log.error(f'[{self.account_name}] Failed to get boosts list.')
            self.SendTelegramLog(
                f'[{self.account_name}] Failed to get boosts list.',
                'other_errors',
            )
            return None

        BoostForTapList = None
        for boost in BoostList['boostsForBuy']:
            if boost['price'] == 0 and boost['id'] == 'BoostFullAvailableTaps':
                BoostForTapList = boost
                break

        if (
            BoostForTapList is not None
            and 'price' in BoostForTapList
            and 'cooldownSeconds' in BoostForTapList
            and BoostForTapList['price'] == 0
            and BoostForTapList['cooldownSeconds'] == 0
        ):
            log.info(
                f'[{self.account_name}] Free boost found, attempting to buy...'
            )
            time.sleep(5)
            self.BuyBoostRequest(BoostForTapList['id'])
            log.info(f'[{self.account_name}] Free boost bought successfully')
            return True
        else:
            log.info(
                f'\033[1;34m[{self.account_name}] No free boosts available\033[0m'
            )

        return False

    def IPRequest(self):
        url = 'https://api.hamsterkombatgame.io/ip'
        headers = {
            'Access-Control-Request-Headers': 'authorization',
            'Access-Control-Request-Method': 'GET',
        }

        # Send OPTIONS request
        self.HttpRequest(url, headers, 'OPTIONS', 200)

        headers = {
            'Authorization': self.Authorization,
        }

        # Send GET request
        return self.HttpRequest(url, headers, 'GET', 200)

    def AccountInfoTelegramRequest(self):
        url = 'https://api.hamsterkombatgame.io/auth/account-info'
        headers = {
            'Access-Control-Request-Headers': 'authorization',
            'Access-Control-Request-Method': 'POST',
        }

        # Send OPTIONS request
        self.HttpRequest(url, headers, 'OPTIONS', 204)

        headers = {
            'Authorization': self.Authorization,
        }

        # Send POST request
        return self.HttpRequest(url, headers, 'POST', 200)

    def ListTasksRequest(self):
        url = 'https://api.hamsterkombatgame.io/clicker/list-tasks'
        headers = {
            'Access-Control-Request-Headers': 'authorization',
            'Access-Control-Request-Method': 'POST',
        }

        # Send OPTIONS request
        self.HttpRequest(url, headers, 'OPTIONS', 204)

        headers = {
            'Authorization': self.Authorization,
        }

        # Send POST request
        return self.HttpRequest(url, headers, 'POST', 200)

    def GetListAirDropTasksRequest(self):
        url = 'https://api.hamsterkombatgame.io/clicker/list-airdrop-tasks'
        headers = {
            'Access-Control-Request-Headers': 'authorization',
            'Access-Control-Request-Method': 'POST',
        }

        # Send OPTIONS request
        self.HttpRequest(url, headers, 'OPTIONS', 204)

        headers = {
            'Authorization': self.Authorization,
        }

        # Send POST request
        return self.HttpRequest(url, headers, 'POST', 200)

    def GetAccountConfigRequest(self):
        url = 'https://api.hamsterkombatgame.io/clicker/config'
        headers = {
            'Access-Control-Request-Headers': 'authorization',
            'Access-Control-Request-Method': 'POST',
        }

        # Send OPTIONS request
        self.HttpRequest(url, headers, 'OPTIONS', 204)

        headers = {
            'Authorization': self.Authorization,
        }

        # Send POST request
        return self.HttpRequest(url, headers, 'POST', 200)

    def GetConfigURLRequest(self, config_version):
        url = (
            'https://api.hamsterkombatgame.io/clicker/config/' + config_version
        )
        headers = {
            'Access-Control-Request-Headers': '*',
            'Access-Control-Request-Method': '*',
        }

        # Send OPTIONS request
        self.HttpRequest(url, headers, 'OPTIONS', 204)

        headers = {
            'Authorization': self.Authorization,
        }

        # Send POST request
        return self.HttpRequest(url, headers, 'GET', 200)

    # Sending get-skin request
    def GetSkinRequest(self):
        url = 'https://api.hamsterkombatgame.io/clicker/get-skin'
        headers = {
            'Access-Control-Request-Headers': self.Authorization,
            'Access-Control-Request-Method': 'POST',
        }

        # Send OPTIONS request
        self.HttpRequest(url, headers, 'OPTIONS', 204)

        headers = {
            'Accept': 'application/json',
            'Authorization': self.Authorization,
            'Content-Type': 'application/json',
        }

        # Send POST request
        return self.HttpRequest(url, headers, 'POST', 200)

    # Sending buy-skin request
    def BuySkinRequest(self, skinId):
        url = 'https://api.hamsterkombatgame.io/clicker/buy-skin'
        headers = {
            'Access-Control-Request-Headers': self.Authorization,
            'Access-Control-Request-Method': 'POST',
        }

        # Send OPTIONS request
        self.HttpRequest(url, headers, 'OPTIONS', 204)

        headers = {
            'Accept': 'application/json',
            'Authorization': self.Authorization,
            'Content-Type': 'application/json',
        }

        payload = json.dumps(
            {
                'skinId': skinId,
                'timestamp': int(datetime.datetime.now().timestamp() * 1000),
            }
        )

        # Send POST request
        return self.HttpRequest(url, headers, 'POST', 200, payload)

    def ClaimDailyCipherRequest(self, DailyCipher):
        url = 'https://api.hamsterkombatgame.io/clicker/claim-daily-cipher'
        headers = {
            'Access-Control-Request-Headers': 'authorization,content-type',
            'Access-Control-Request-Method': 'POST',
        }

        # Send OPTIONS request
        self.HttpRequest(url, headers, 'OPTIONS', 204)

        headers = {
            'Accept': 'application/json',
            'Authorization': self.Authorization,
            'Content-Type': 'application/json',
        }

        payload = json.dumps(
            {
                'cipher': DailyCipher,
            }
        )

        # Send POST request
        return self.HttpRequest(url, headers, 'POST', 200, payload)

    def CheckTaskRequest(self, task_id):
        url = 'https://api.hamsterkombatgame.io/clicker/check-task'
        headers = {
            'Access-Control-Request-Headers': 'authorization,content-type',
            'Access-Control-Request-Method': 'POST',
        }

        # Send OPTIONS request
        self.HttpRequest(url, headers, 'OPTIONS', 204)

        headers = {
            'Accept': 'application/json',
            'Authorization': self.Authorization,
            'Content-Type': 'application/json',
        }

        payload = json.dumps(
            {
                'taskId': task_id,
            }
        )

        # Send POST request
        return self.HttpRequest(url, headers, 'POST', 200, payload)

    def BuyCard(self, card):
        upgradesResponse = self.BuyUpgradeRequest(card['id'])

        if upgradesResponse is None:
            log.error(f'[{self.account_name}] Failed to buy the card.')
            self.SendTelegramLog(
                f'[{self.account_name}] Failed to buy the card.',
                'other_errors',
            )
            return False

        log.info(f'[{self.account_name}] Card bought successfully')
        time.sleep(3)
        self.balanceCoins -= card['price']
        self.ProfitPerHour += card['profitPerHourDelta']
        self.SpendTokens += card['price']
        self.earnPassivePerHour += card['profitPerHourDelta']

        return True

    def BuyBestCard(self):
        log.info(f'[{self.account_name}] Checking for best card...')
        time.sleep(2)
        upgradesResponse = self.UpgradesForBuyRequest()

        if upgradesResponse is None:
            log.error(f'[{self.account_name}] Failed to get upgrades list.')
            self.SendTelegramLog(
                f'[{self.account_name}] Failed to get upgrades list.',
                'other_errors',
            )
            return False

        if upgradesResponse.get('dailyCombo'):
            if upgradesResponse.get('dailyCombo').get('isClaimed'):
                self.ClaimDailyComboRequest()
                log.info(
                    f'[{self.account_name}] Daily Combo completed successfully.'
                )

        upgrades = [
            item
            for item in upgradesResponse['upgradesForBuy']
            if not item['isExpired']
            and item['isAvailable']
            and item['profitPerHourDelta'] > 0
        ]

        if len(upgrades) == 0:
            log.warning(f'[{self.account_name}] No upgrades available.')
            return False

        balanceCoins = int(self.balanceCoins)
        log.info(f'[{self.account_name}] Searching for the best upgrades...')

        selected_upgrades = SortUpgrades(
            upgrades, 999_999_999_999
        )  # Set max budget to a high number
        if len(selected_upgrades) == 0:
            log.warning(f'[{self.account_name}] No upgrades available.')
            return False

        current_selected_card = selected_upgrades[0]
        for selected_card in selected_upgrades:
            if (
                'cooldownSeconds' in selected_card
                and selected_card['cooldownSeconds'] > 0
                and selected_card['cooldownSeconds'] < 180
            ):
                log.warning(
                    f"[{self.account_name}] {selected_card['name']} is on cooldown and cooldown is less than 180 seconds..."
                )
                log.warning(
                    f"[{self.account_name}] Waiting for {selected_card['cooldownSeconds'] + 2} seconds..."
                )

                time.sleep(selected_card['cooldownSeconds'] + 2)
                selected_card['cooldownSeconds'] = 0

            if (
                'cooldownSeconds' in selected_card
                and selected_card['cooldownSeconds'] > 0
                and not self.config['enable_parallel_upgrades']
            ):
                log.warning(
                    f"[{self.account_name}] {selected_card['name']} is on cooldown..."
                )
                return False

            if (
                'cooldownSeconds' in selected_card
                and selected_card['cooldownSeconds'] > 0
            ):
                log.warning(
                    f"[{self.account_name}] {selected_card['name']} is on cooldown, Checking for next card..."
                )
                continue

            if (
                CalculateCardProfitCoefficient(selected_card)
                > self.config['parallel_upgrades_max_price_per_hour']
                and self.config['enable_parallel_upgrades']
            ):
                log.warning(
                    f"[{self.account_name}] {selected_card['name']} is too expensive to buy in parallel..."
                )
                return False

            current_selected_card = selected_card
            break

        log.info(
            f"[{self.account_name}] Best upgrade is {current_selected_card['name']} with profit {current_selected_card['profitPerHourDelta']} and price {number_to_string(current_selected_card['price'])}, Level: {current_selected_card['level']}"
        )

        if balanceCoins < current_selected_card['price']:
            log.warning(
                f'[{self.account_name}] Balance is too low to buy the best card.'
            )

            self.SendTelegramLog(
                f"[{self.account_name}] Balance is too low to buy the best card, Best card: {current_selected_card['name']} with profit {current_selected_card['profitPerHourDelta']} and price {number_to_string(current_selected_card['price'])}, Level: {current_selected_card['level']}",
                'upgrades',
            )
            return False

        log.info(f'[{self.account_name}] Attempting to buy the best card...')
        buy_result = self.BuyCard(current_selected_card)

        if buy_result:
            time.sleep(2)
            log.info(
                f'[{self.account_name}] Best card purchase completed successfully, Your profit per hour increased by {number_to_string(self.ProfitPerHour)} coins, Spend tokens: {number_to_string(self.SpendTokens)}'
            )
            self.SendTelegramLog(
                f"[{self.account_name}] Bought {current_selected_card['name']} with profit {current_selected_card['profitPerHourDelta']} and price {number_to_string(current_selected_card['price'])}, Level: {current_selected_card['level']}",
                'upgrades',
            )

            return True
        return False

    def StartMiniGame(self, AccountConfigData, AccountID):
        if 'dailyKeysMiniGame' not in AccountConfigData:
            log.error(
                f'[{self.account_name}] Unable to get daily keys mini game.'
            )
            self.SendTelegramLog(
                f'[{self.account_name}] Unable to get daily keys mini game.',
                'other_errors',
            )
            return

        if AccountConfigData['dailyKeysMiniGame']['isClaimed'] == True:
            log.info(
                f'\033[1;34m[{self.account_name}] Daily keys mini game already claimed.\033[0m'
            )
            return

        if (
            AccountConfigData['dailyKeysMiniGame'][
                'remainSecondsToNextAttempt'
            ]
            > 0
        ):
            log.info(
                f'[{self.account_name}] Daily keys mini game is on cooldown...'
            )
            return

        # check timer.
        url = 'https://api.hamsterkombatgame.io/clicker/start-keys-minigame'

        headers = {
            'Access-Control-Request-Headers': 'authorization',
            'Access-Control-Request-Method': 'POST',
        }

        # Send OPTIONS request
        self.HttpRequest(url, headers, 'OPTIONS', 204)

        headers = {
            'Authorization': self.Authorization,
        }

        # Send POST request
        response = self.HttpRequest(url, headers, 'POST', 200)

        if response is None:
            log.error(f'[{self.account_name}] Unable to start mini game.')
            self.SendTelegramLog(
                f'[{self.account_name}] Unable to start mini game.',
                'other_errors',
            )
            return

        if 'dailyKeysMiniGame' not in response:
            log.error(
                f'[{self.account_name}] Unable to get daily keys mini game.'
            )
            self.SendTelegramLog(
                f'[{self.account_name}] Unable to get daily keys mini game.',
                'other_errors',
            )
            return

        if response['dailyKeysMiniGame']['isClaimed'] == True:
            log.info(
                f'\033[1;34m[{self.account_name}] Daily keys mini game already claimed.\033[0m'
            )
            return

        if 'remainSecondsToGuess' not in response['dailyKeysMiniGame']:
            log.error(
                f'[{self.account_name}] Unable to get daily keys mini game.'
            )
            self.SendTelegramLog(
                f'[{self.account_name}] Unable to get daily keys mini game.',
                'other_errors',
            )
            return

        waitTime = int(
            response['dailyKeysMiniGame']['remainSecondsToGuess']
            - random.randint(8, 15)
        )

        if waitTime < 0:
            log.error(f'[{self.account_name}] Unable to claim mini game.')
            self.SendTelegramLog(
                f'[{self.account_name}] Unable to claim mini game.',
                'other_errors',
            )
            return

        log.info(
            f'[{self.account_name}] Waiting for {waitTime} seconds, Mini-game will be completed in {waitTime} seconds...'
        )
        time.sleep(waitTime)

        url = 'https://api.hamsterkombatgame.io/clicker/claim-daily-keys-minigame'

        headers = {
            'Access-Control-Request-Headers': 'authorization,content-type',
            'Access-Control-Request-Method': 'POST',
        }

        # Send OPTIONS request
        self.HttpRequest(url, headers, 'OPTIONS', 204)

        headers = {
            'Accept': 'application/json',
            'Authorization': self.Authorization,
            'Content-Type': 'application/json',
        }

        cipher = (
            (
                '0'
                + str(waitTime)
                + str(random.randint(10000000000, 99999999999))
            )[:10]
            + '|'
            + str(AccountID)
        )
        cipher_base64 = base64.b64encode(cipher.encode()).decode()

        payload = json.dumps(
            {
                'cipher': cipher_base64,
            }
        )

        # Send POST request
        response = self.HttpRequest(url, headers, 'POST', 200, payload)

        if response is None:
            log.error(f'[{self.account_name}] Unable to claim mini game.')
            self.SendTelegramLog(
                f'[{self.account_name}] Unable to claim mini game.',
                'other_errors',
            )
            return

        log.info(f'[{self.account_name}] Mini game claimed successfully.')

    def StartPlaygroundGame(self):
        if not self.config['auto_playground_games']:
            log.info(f'[{self.account_name}] Playground games are disabled.')
            return

        log.info(
            f'[{self.account_name}] Starting gettting playground games...'
        )

        url = 'https://api.hamsterkombatgame.io/clicker/get-promos'
        headers = {
            'Access-Control-Request-Headers': 'authorization',
            'Access-Control-Request-Method': 'POST',
        }

        # Send OPTIONS request
        self.HttpRequest(url, headers, 'OPTIONS', 204)

        headers = {
            'Authorization': self.Authorization,
        }

        # Send POST request
        response = self.HttpRequest(url, headers, 'POST', 200)

        if response is None:
            log.error(f'[{self.account_name}] Unable to get playground games.')
            self.SendTelegramLog(
                f'[{self.account_name}] Unable to get playground games.',
                'other_errors',
            )
            return

        if 'promos' not in response:
            log.error(f'[{self.account_name}] Unable to get playground games.')
            self.SendTelegramLog(
                f'[{self.account_name}] Unable to get playground games.',
                'other_errors',
            )
            return

        promo_count = 0
        for promo in response['promos']:
            if promo['promoId'] not in SupportedPromoGames:
                log.warning(
                    f"[{self.account_name}] Detected unknown playground game: {promo['title']['en']}. Check project github for updates."
                )
                continue

            if self.CheckPlayGroundGameState(promo, response):
                promoData = SupportedPromoGames[promo['promoId']]

                promo_count += 1
                if self.GetConfig(
                    'max_promo_games_per_round', 3
                ) != 0 and promo_count > self.GetConfig(
                    'max_promo_games_per_round', 3
                ):
                    log.info(
                        f'[{self.account_name}] Maximum number of playground games reached. We will retrieve other games in the next run.'
                    )
                    return
                log.info(
                    f"[{self.account_name}] Starting {promoData['name']} Playground game..."
                )
                time.sleep(1)
                promoCode = self.GetPlayGroundGameKey(promoData)
                if promoCode is not None:
                    log.info(
                        f"\033[1;34m[{self.account_name}] {promoData['name']} key: {promoCode}\033[0m"
                    )
                    time.sleep(2)
                    log.info(
                        f"[{self.account_name}] Claiming {promoData['name']}..."
                    )
                    self.ClaimPlayGroundGame(promoCode)
                    log.info(
                        f"[{self.account_name}] {promoData['name']} claimed successfully."
                    )

    def ClaimPlayGroundGame(self, promoCode):
        url = 'https://api.hamsterkombatgame.io/clicker/apply-promo'

        headers = {
            'Access-Control-Request-Headers': 'authorization,content-type',
            'Access-Control-Request-Method': 'POST',
        }

        # Send OPTIONS request
        self.HttpRequest(url, headers, 'OPTIONS', 204)

        headers = {
            'Accept': 'application/json',
            'Authorization': self.Authorization,
            'Content-Type': 'application/json',
        }

        payload = json.dumps(
            {
                'promoCode': promoCode,
            }
        )

        # Send POST request
        return self.HttpRequest(url, headers, 'POST', 200, payload)

    def GetPlayGroundGameKey(self, promoData):
        appToken = promoData['appToken']
        clientId = f"{int(time.time() * 1000)}-{''.join(str(random.randint(0, 9)) for _ in range(19))}"

        log.info(f"[{self.account_name}] Getting {promoData['name']} key...")
        url = 'https://api.gamepromo.io/promo/login-client'

        headers_option = {
            'Host': 'api.gamepromo.io',
            'Origin': '',
            'Referer': '',
            'access-control-request-headers': 'content-type',
            'access-control-request-method': 'POST',
        }

        self.HttpRequest(url, headers_option, 'OPTIONS', 204, True)

        headers = {
            'Content-Type': 'application/json; charset=utf-8',
            'Host': 'api.gamepromo.io',
            'Origin': '',
            'Referer': '',
        }

        payload = json.dumps(
            {
                'appToken': appToken,
                'clientId': clientId,
                'clientOrigin': 'ios',
            }
        )

        response = self.HttpRequest(url, headers, 'POST', 200, payload)
        if response is None:
            log.error(
                f"[{self.account_name}] Unable to get {promoData['name']} key."
            )
            self.SendTelegramLog(
                f"[{self.account_name}] Unable to get {promoData['name']} key.",
                'other_errors',
            )
            return None

        if 'clientToken' not in response:
            log.error(
                f"[{self.account_name}] Unable to get {promoData['name']} key."
            )
            self.SendTelegramLog(
                f"[{self.account_name}] Unable to get {promoData['name']} key.",
                'other_errors',
            )
            return None

        clientToken = response['clientToken']

        time.sleep(promoData['delay'] + random.randint(1, 5))

        log.info(
            f"[{self.account_name}] Registering event for {promoData['name']}..."
        )

        url = 'https://api.gamepromo.io/promo/register-event'

        headers = {
            'Authorization': f'Bearer {clientToken}',
            'Host': 'api.gamepromo.io',
            'Content-Type': 'application/json; charset=utf-8',
            'Origin': '',
            'Referer': '',
        }

        response = None

        retryCount = 0
        while retryCount < 12:
            retryCount += 1
            eventID = str(uuid.uuid4())

            headers_option[
                'access-control-request-headers'
            ] = 'authorization,content-type'

            self.HttpRequest(url, headers_option, 'OPTIONS', 204, True)

            PayloadData = {
                'promoId': promoData['promoId'],
                'eventId': eventID,
                'eventOrigin': 'undefined',
            }

            if 'eventType' in promoData and promoData['eventType'] != None:
                PayloadData['eventType'] = promoData['eventType']

            payload = json.dumps(PayloadData)

            response = self.HttpRequest(
                url, headers, 'POST', 200, payload, True
            )

            if response is None or not isinstance(response, dict):
                time.sleep(promoData['retry_delay'] + random.randint(1, 5))
                continue

            if not response.get('hasCode', False):
                time.sleep(promoData['retry_delay'] + random.randint(1, 5))
                continue

            break

        if (
            response is None
            or not isinstance(response, dict)
            or 'hasCode' not in response
        ):
            log.error(f'[{self.account_name}] Unable to register event.')
            self.SendTelegramLog(
                f'[{self.account_name}] Unable to register event.',
                'other_errors',
            )
            return None

        log.info(f'[{self.account_name}] Event registered successfully.')

        url = 'https://api.gamepromo.io/promo/create-code'

        headers = {
            'Authorization': f'Bearer {clientToken}',
            'Content-Type': 'application/json; charset=utf-8',
            'Host': 'api.gamepromo.io',
            'Origin': '',
            'Referer': '',
        }

        headers_option[
            'access-control-request-headers'
        ] = 'authorization,content-type'

        self.HttpRequest(url, headers_option, 'OPTIONS', 204, True)

        payload = json.dumps(
            {
                'promoId': promoData['promoId'],
            }
        )

        response = self.HttpRequest(url, headers, 'POST', 200, payload)
        if response is None:
            log.error(
                f"[{self.account_name}] Unable to get {promoData['name']} key."
            )
            self.SendTelegramLog(
                f"[{self.account_name}] Unable to get {promoData['name']} key.",
                'other_errors',
            )
            return None

        if (
            'promoCode' not in response
            or response.get('promoCode') is None
            or response.get('promoCode') == ''
        ):
            log.error(
                f"[{self.account_name}] Unable to get {promoData['name']} key."
            )
            self.SendTelegramLog(
                f"[{self.account_name}] Unable to get {promoData['name']} key.",
                'other_errors',
            )
            return None

        promoCode = response['promoCode']
        return promoCode

    def CheckPlayGroundGameState(self, promo, promos):
        if not self.config['auto_playground_games']:
            log.info(f'[{self.account_name}] Playground games are disabled.')
            return False

        if promo['promoId'] not in SupportedPromoGames:
            return False

        if 'states' not in promos:
            return True

        for state in promos['states']:
            if (
                state['promoId'] == promo['promoId']
                and state['receiveKeysToday'] >= promo['keysPerDay']
            ):
                log.info(
                    f"\033[1;34m[{self.account_name}] Playground game {SupportedPromoGames[promo['promoId']]['name']} already claimed.\033[0m"
                )
                return False

        return True

    def Start(self):
        log.info(f'[{self.account_name}] Starting account...')

        log.info(f'[{self.account_name}] Getting basic account data...')
        AccountBasicData = self.AccountInfoTelegramRequest()

        if (
            AccountBasicData is None
            or AccountBasicData is False
            or 'accountInfo' not in AccountBasicData
            or 'id' not in AccountBasicData['accountInfo']
        ):
            log.error(
                f'[{self.account_name}] Unable to get account basic data.'
            )
            self.SendTelegramLog(
                f'[{self.account_name}] Unable to get account basic data.',
                'other_errors',
            )
            return

        log.info(
            f"\033[1;35m[{self.account_name}] Account ID: {AccountBasicData['accountInfo']['id']}, Account Name: {AccountBasicData['accountInfo']['name']}\033[0m"
        )
        self.SendTelegramLog(
            f"[{self.account_name}] Account ID: {AccountBasicData['accountInfo']['id']}",
            'account_info',
        )

        log.info(f'[{self.account_name}] Getting account config data...')

        try:
            AccountConfigData = self.GetAccountConfigRequest()
            if not self.Config_Version:
                raise ValueError(
                    'No Config-Version to generate a link to get the config.'
                )
            AccountConfigURLData = self.GetConfigURLRequest(
                self.Config_Version
            )
            if (
                AccountConfigData is None
                or AccountConfigURLData is None
                or AccountConfigData is False
                or AccountConfigURLData is False
                or 'dailyCipher' not in AccountConfigData
                or 'dailyKeysMiniGame' not in AccountConfigData
                or 'config' not in AccountConfigURLData
            ):
                raise ValueError('Incomplete config data.')
            AccountConfigData['clickerConfig'] = AccountConfigURLData['config']
        except (Exception, ValueError, KeyError) as e:
            log.error(
                f'[{self.account_name}] Unable to get account config data. {e}'
            )
            self.SendTelegramLog(
                f'[{self.account_name}] Unable to get account config data. {e}',
                'other_errors',
            )
            return

        DailyCipher = ''
        if (
            self.config['auto_get_daily_cipher']
            and 'dailyCipher' in AccountConfigData
            and 'cipher' in AccountConfigData['dailyCipher']
        ):
            log.info(f'[{self.account_name}] Decoding daily cipher...')
            DailyCipher = DailyCipherDecode(
                AccountConfigData['dailyCipher']['cipher']
            )
            MorseCode = TextToMorseCode(DailyCipher)
            log.info(
                f'\033[1;34m[{self.account_name}] Daily cipher: {DailyCipher} and Morse code: {MorseCode}\033[0m'
            )

        log.info(f'[{self.account_name}] Getting account data...')
        getAccountDataStatus = self.getAccountData()
        if getAccountDataStatus is False:
            return

        log.info(
            f'[{self.account_name}] Account Balance Coins: {number_to_string(self.balanceCoins)}, Available Taps: {self.availableTaps}, Max Taps: {self.maxTaps}, Total Keys: {self.totalKeys}, Balance Keys: {self.balanceKeys}'
        )

        log.info(f'[{self.account_name}] Getting account upgrades...')
        upgradesResponse = self.UpgradesForBuyRequest()

        if upgradesResponse is None:
            log.error(f'[{self.account_name}] Failed to get upgrades list.')
            self.SendTelegramLog(
                f'[{self.account_name}] Failed to get upgrades list.',
                'other_errors',
            )
            return

        log.info(f'[{self.account_name}] Getting account skins...')
        skinsResponse = self.GetSkinRequest()

        if skinsResponse is None:
            log.error(f'[{self.account_name}] Failed to get skins list.')
            self.SendTelegramLog(
                f'[{self.account_name}] Failed to get skins list.',
                'other_errors',
            )
            return

        log.info(f'[{self.account_name}] Getting account tasks...')
        tasksResponse = self.ListTasksRequest()

        if tasksResponse is None:
            log.error(f'[{self.account_name}] Failed to get tasks list.')
            self.SendTelegramLog(
                f'[{self.account_name}] Failed to get tasks list.',
                'other_errors',
            )

        log.info(f'[{self.account_name}] Getting account airdrop tasks...')
        airdropTasksResponse = self.GetListAirDropTasksRequest()

        if airdropTasksResponse is None:
            log.error(
                f'[{self.account_name}] Failed to get airdrop tasks list.'
            )

        log.info(f'[{self.account_name}] Getting account IP...')
        ipResponse = self.IPRequest()
        if ipResponse is None:
            log.error(f'[{self.account_name}] Failed to get IP.')
            self.SendTelegramLog(
                f'[{self.account_name}] Failed to get IP.', 'other_errors'
            )
            return

        log.info(
            f"[{self.account_name}] IP: {ipResponse['ip']} Company: {ipResponse['asn_org']} Country: {ipResponse['country_code']}"
        )

        if self.config['auto_finish_mini_game']:
            log.info(
                f'[{self.account_name}] Attempting to finish mini game...'
            )
            time.sleep(1)
            self.StartMiniGame(
                AccountConfigData, AccountBasicData['accountInfo']['id']
            )

        # Start tapping
        if self.config['auto_tap']:
            log.info(f'[{self.account_name}] Starting to tap...')
            time.sleep(2)
            self.TapRequest(self.availableTaps)
            log.info(f'[{self.account_name}] Tapping completed successfully.')

        if self.config['auto_get_daily_cipher'] and DailyCipher != '':
            if AccountConfigData['dailyCipher']['isClaimed'] == True:
                log.info(
                    f'\033[1;34m[{self.account_name}] Daily cipher already claimed.\033[0m'
                )
            else:
                log.info(
                    f'[{self.account_name}] Attempting to claim daily cipher...'
                )
                time.sleep(2)
                self.ClaimDailyCipherRequest(DailyCipher)
                log.info(
                    f'[{self.account_name}] Daily cipher claimed successfully.'
                )
                self.SendTelegramLog(
                    f'[{self.account_name}] Daily cipher claimed successfully. Text was: {DailyCipher}, Morse code was: {TextToMorseCode(DailyCipher)}',
                    'daily_cipher',
                )

        if (
            self.config['auto_get_daily_task']
            and tasksResponse is not None
            and 'tasks' in tasksResponse
            and isinstance(tasksResponse['tasks'], list)
        ):
            log.info(f'[{self.account_name}] Checking for daily task...')
            streak_days = None
            for task in tasksResponse.get('tasks', []):
                if task['id'] == 'streak_days':
                    streak_days = task
                    break

            if streak_days is None:
                log.error(f'[{self.account_name}] Failed to get daily task.')
                return

            if streak_days['isCompleted'] == True:
                log.info(
                    f'\033[1;34m[{self.account_name}] Daily task already completed.\033[0m'
                )
            else:
                log.info(
                    f'[{self.account_name}] Attempting to complete daily task...'
                )
                day = streak_days['days']
                rewardCoins = streak_days['rewardCoins']
                time.sleep(2)
                self.CheckTaskRequest('streak_days')
                log.info(
                    f'[{self.account_name}] Daily task completed successfully, Day: {day}, Reward coins: {number_to_string(rewardCoins)}'
                )
                self.SendTelegramLog(
                    f'[{self.account_name}] Daily task completed successfully, Day: {day}, Reward coins: {number_to_string(rewardCoins)}',
                    'daily_task',
                )

        if self.config['auto_get_task']:
            log.info(f'[{self.account_name}] Checking for available task...')
            selected_task = None
            if not tasksResponse:
                return
            for task in tasksResponse.get('tasks', []):
                if task.get('linksWithLocales'):
                    link = task.get('linksWithLocales').get('en', '')
                else:
                    link = task.get('link', '')
                if not task['isCompleted'] and ('https://' in link):
                    log.info(
                        f'[{self.account_name}] Attempting to complete Youtube Or Twitter task...'
                    )
                    selected_task = task['id']
                    rewardCoins = task['rewardCoins']
                    time.sleep(2)
                    self.CheckTaskRequest(selected_task)
                    log.info(
                        f'[{self.account_name}] Task completed - id: {selected_task}, Reward coins: {number_to_string(rewardCoins)}'
                    )
                    self.SendTelegramLog(
                        f'[{self.account_name}] Task completed - id: {selected_task}, Reward coins: {number_to_string(rewardCoins)}',
                        'daily_task',
                    )
            if selected_task is None:
                log.info(
                    f'\033[1;34m[{self.account_name}] Tasks already done\033[0m'
                )

        # Start buying free tap boost
        if (
            self.config['auto_tap']
            and self.config['auto_free_tap_boost']
            and self.BuyFreeTapBoostIfAvailable()
        ):
            log.info(
                f'[{self.account_name}] Starting to tap with free boost...'
            )
            time.sleep(2)
            self.TapRequest(self.availableTaps)
            log.info(
                f'[{self.account_name}] Tapping with free boost completed successfully.'
            )

        # Start Syncing account data after tapping
        if self.config['auto_tap']:
            self.getAccountData()
            log.info(
                f'[{self.account_name}] Account Balance Coins: {number_to_string(self.balanceCoins)}, Available Taps: {self.availableTaps}, Max Taps: {self.maxTaps}, Total Keys: {self.totalKeys}, Balance Keys: {self.balanceKeys}'
            )

        self.StartPlaygroundGame()
        # Start skins upgrades
        AccountConfigData['clickerConfig']
        if (
            self.config['auto_get_skin']
            and 'skins' in AccountConfigData['clickerConfig']
        ):
            log.info(f'[{self.account_name}] Starting to get skin...')
            self.getAccountData()
            sorted_skins = sorted(
                AccountConfigData['clickerConfig']['skins'],
                key=lambda x: x['price'],
            )

            for skin in sorted_skins:
                skins_available = [
                    val
                    for sublist in self.availableSkins['available']
                    for val in sublist.values()
                ]
                if (
                    skin['id'] != 'skin0'
                    and skin['id'] not in skins_available
                    and skin['condition']['level'] <= self.level
                ):
                    if self.balanceCoins < skin['price']:
                        continue
                    time.sleep(2)
                    buySkinResponse = self.BuySkinRequest(skin['id'])

                    if buySkinResponse:
                        log.info(
                            f"[{self.account_name}] Skin {skin['name']} get price {skin['price']}"
                        )
                        self.getAccountData()

        # Start buying upgrades
        if not self.config['auto_upgrade']:
            log.error(f'[{self.account_name}] Auto upgrade is disabled.')
            return

        self.ProfitPerHour = 0
        self.SpendTokens = 0

        if self.config['wait_for_best_card']:
            while True:
                if not self.BuyBestCard():
                    break

            self.getAccountData()
            log.info(
                f'[{self.account_name}] Final account balance: {number_to_string(self.balanceCoins)} coins, Your profit per hour is {number_to_string(self.earnPassivePerHour)} (+{number_to_string(self.ProfitPerHour)}), Spent: {number_to_string(self.SpendTokens)}'
            )
            self.SendTelegramLog(
                f'[{self.account_name}] Final account balance: {number_to_string(self.balanceCoins)} coins, Your profit per hour is {number_to_string(self.earnPassivePerHour)} (+{number_to_string(self.ProfitPerHour)}), Spent: {number_to_string(self.SpendTokens)}',
                'upgrades',
            )
            return

        if self.balanceCoins < self.config['auto_upgrade_start']:
            log.warning(
                f'[{self.account_name}] Balance is too low to start buying upgrades.'
            )
            return

        while self.balanceCoins >= self.config['auto_upgrade_min']:
            log.info(f'[{self.account_name}] Checking for upgrades...')
            time.sleep(2)
            upgradesResponse = self.UpgradesForBuyRequest()
            if upgradesResponse is None:
                log.warning(
                    f'[{self.account_name}] Failed to get upgrades list.'
                )
                self.SendTelegramLog(
                    f'[{self.account_name}] Failed to get upgrades list.',
                    'other_errors',
                )
                return

            upgrades = [
                item
                for item in upgradesResponse['upgradesForBuy']
                if not item['isExpired']
                and item['isAvailable']
                and item['profitPerHourDelta'] > 0
                and (
                    'cooldownSeconds' not in item
                    or item['cooldownSeconds'] == 0
                )
            ]

            if len(upgrades) == 0:
                log.warning(f'[{self.account_name}] No upgrades available.')
                return

            balanceCoins = int(self.balanceCoins)
            log.info(
                f'[{self.account_name}] Searching for the best upgrades...'
            )

            selected_upgrades = SortUpgrades(upgrades, balanceCoins)
            if len(selected_upgrades) == 0:
                log.warning(f'[{self.account_name}] No upgrades available.')
                return

            current_selected_card = selected_upgrades[0]
            log.info(
                f"[{self.account_name}] Best upgrade is {current_selected_card['name']} with profit {current_selected_card['profitPerHourDelta']} and price {number_to_string(current_selected_card['price'])}, Level: {current_selected_card['level']}"
            )

            balanceCoins -= current_selected_card['price']

            log.info(f'[{self.account_name}] Attempting to buy an upgrade...')
            time.sleep(2)
            upgradesResponse = self.BuyUpgradeRequest(
                current_selected_card['id']
            )
            if upgradesResponse is None:
                log.error(f'[{self.account_name}] Failed to buy an upgrade.')
                return

            log.info(f'[{self.account_name}] Upgrade bought successfully')
            self.SendTelegramLog(
                f"[{self.account_name}] Bought {current_selected_card['name']} with profit {current_selected_card['profitPerHourDelta']} and price {number_to_string(current_selected_card['price'])}, Level: {current_selected_card['level']}",
                'upgrades',
            )
            time.sleep(5)
            self.balanceCoins = balanceCoins
            self.ProfitPerHour += current_selected_card['profitPerHourDelta']
            self.SpendTokens += current_selected_card['price']
            self.earnPassivePerHour += current_selected_card[
                'profitPerHourDelta'
            ]

        log.info(
            f'[{self.account_name}] Upgrades purchase completed successfully.'
        )
        self.getAccountData()
        log.info(
            f'[{self.account_name}] Final account balance: {number_to_string(self.balanceCoins)} coins, Your profit per hour is {number_to_string(self.earnPassivePerHour)} (+{number_to_string(self.ProfitPerHour)}), Spent: {number_to_string(self.SpendTokens)}'
        )
        self.SendTelegramLog(
            f'[{self.account_name}] Final account balance: {number_to_string(self.balanceCoins)} coins, Your profit per hour is {number_to_string(self.earnPassivePerHour)} (+{number_to_string(self.ProfitPerHour)}), Spent: {number_to_string(self.SpendTokens)}',
            'account_info',
        )


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
