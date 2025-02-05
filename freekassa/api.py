import hashlib
from urllib.parse import urlencode
import aiohttp
import ujson


class FreeKassaApi:
    base_url = 'https://www.free-kassa.ru/api.php'
    base_form_url = 'https://pay.freekassa.ru/'
    base_export_order_url = 'https://www.free-kassa.ru/export.php'
    wallet_api_url = 'https://www.fkwallet.ru/api_v1.php'

    def __init__(self, merchant_id, first_secret,
                 second_secret, wallet_id, wallet_api_key=''):
        self.merchant_id = merchant_id
        self.first_secret = first_secret
        self.second_secret = second_secret
        self.wallet_id = wallet_id
        self.wallet_api_key = wallet_api_key

    async def send_request(self, params, url=None, method='post'):
        """
        Send request to freekassa api
        :param url:
        :param params:params
        :param method:method
        :return:
        """
        if url is None:
            url = self.base_url
        
        async with aiohttp.ClientSession(json_serialize=ujson.dumps,
                                         raise_for_status=True) as session:
            return await session.__dict__[method](url, params=params)

    async def get_balance(self):
        """
        Get merchant balance
        :return:
        """
        params = {
            'merchant_id': self.merchant_id,
            's': await self.generate_api_signature(),
            'action': 'get_balance',
        }

        return await self.send_request(params=params)

    async def get_order(self, order_id='', int_id=''):
        """
        :return:
        """
        params = {
            'merchant_id': self.merchant_id,
            's': await self.generate_api_signature(),
            'action': 'check_order_status',
            'order_id': order_id,
            'intid': int_id,
        }

        return await self.send_request(params=params)

    async def export_order(self, status, date_from, date_to, limit=0, offset=100):
        """
        Get orders list.
        :param status:
        :param date_from:
        :param date_to:
        :param limit:
        :param offset:
        :return:
        """
        params = {
            'merchant_id': self.merchant_id,
            's': await self.generate_api_signature(),
            'action': 'get_orders',
            'date_from': date_from,
            'date_to': date_to,
            'status': status,
            'limit': limit,
            'offset': offset,
        }

        return await self.send_request(params=params)

    async def withdraw(self, amount, currency):
        """
        Withdraw money.
        :param amount:
        :param currency:
        :return:
        """
        params = {
            'merchant_id': self.merchant_id,
            'currency': currency,
            'amount': amount,
            's': await self.generate_api_signature(),
            'action': 'payment',
        }

        return await self.send_request(params=params)

    async def invoice(self, email, amount, description):
        """
        Create invoice.
        :param email:
        :param amount:
        :param description:
        :return:
        """
        params = {
            'merchant_id': self.merchant_id,
            'email': email,
            'amount': amount,
            'desc': description,
            's': await self.generate_api_signature(),
            'action': 'create_bill',
        }

        return await self.send_request(params)

    async def get_wallet_balance(self):
        """
        Get wallet balance.
        :return:
        """
        params = {
            'wallet_id': self.wallet_id,
            'sign': await self.generate_wallet_signature(),
            'action': await self.get_balance(),
        }

        return await self.send_request(params=params, url=self.wallet_api_url)

    async def wallet_withdraw(self, purse, amount, currency,
                        description, disable_exchange=1):
        """
        Withdraw money from wallet.
        :param purse:
        :param amount:
        :param currency:
        :param description:
        :param disable_exchange:
        :return:
        """
        params = {
            'wallet_id': self.wallet_id,
            'purse': purse,
            'amount': amount,
            'desc': description,
            'disable_exchange': disable_exchange,
            'currency': currency,
            'action': 'cashout',
            'sign': await self.__make_hash(params=[
                self.wallet_id,
                currency,
                amount,
                purse,
                self.wallet_api_key
            ]),
        }

        return await self.send_request(params=params, url=self.wallet_api_url)

    async def get_operation_status(self, payment_id):
        """
        Get operation status.
        :param payment_id:
        :return:
        """
        params = {
            'wallet_id': self.wallet_id,
            'payment_id': payment_id,
            'sign': await self.__make_hash(params=[
                self.wallet_id,
                payment_id,
                self.wallet_api_key
            ]),
            'action': 'get_payment_status',
        }

        return await self.send_request(params=params, url=self.wallet_api_url)

    async def transfer_money(self, purse, amount):
        """
        Transfer money to another wallet.
        :param purse:
        :param amount:
        :return:
        """
        params = {
            'wallet_id': self.wallet_id,
            'purse': purse,
            'amount': amount,
            'sign': await self.__make_hash(params=[
                self.wallet_id,
                purse,
                amount,
                self.wallet_api_key
            ]),
            'action': 'transfer',
        }

        return await self.send_request(params=params, url=self.wallet_api_url)

    async def online_payments(self, service_id, account, amount):
        """
        Payment online services.
        :param service_id:
        :param account:
        :param amount:
        :return:
        """
        params = {
            'wallet_id': self.wallet_id,
            'service_id': service_id,
            'account': account,
            'amount': amount,
            'sign': await self.__make_hash(params=[
                self.wallet_id,
                amount,
                account,
                self.wallet_api_key
            ]),
            'action': 'online_payment',
        }

        return await self.send_request(params=params, url=self.wallet_api_url)

    async def get_online_services(self):
        """
        Get list of payment services.
        :return:
        """
        params = {
            'wallet_id': self.wallet_id,
            'sign': await self.generate_wallet_signature(),
            'action': 'providers',
        }

        return await self.send_request(params=params, url=self.wallet_api_url)

    async def get_online_payment_status(self, payment_id):
        """
        Check status online payment.
        :param payment_id:
        :return:
        """
        params = {
            'wallet_id': self.wallet_id,
            'payment_id': payment_id,
            'sign': await self.__make_hash(params=[
                self.wallet_id,
                payment_id,
                self.wallet_api_key
            ]),
            'action': 'check_online_payment',
        }

        return await self.send_request(params=params, url=self.wallet_api_url)

    async def create_btc_address(self):
        """
        Create BTC address.
        :return:
        """
        return await self.create_crypto_address('create_btc_address')

    async def create_ltc_address(self):
        """
        Create LTC address.
        :return:
        """
        return await self.create_crypto_address('create_ltc_address')

    async def create_eth_address(self):
        """
        Create ETH address.
        :return:
        """
        return await self.create_crypto_address('create_eth_address')

    async def create_crypto_address(self, action):
        """
        Create crypto wallet address.
        :param action:
        :return:
        """
        params = {
            'wallet_id': self.wallet_id,
            'sign': await self.generate_wallet_signature(),
            'action': action,
        }

        return await self.send_request(params=params, url=self.wallet_api_url)

    async def get_btc_address(self):
        """
        Get BTC address.
        :return:
        """
        return await self.get_crypto_address('get_btc_address')

    async def get_ltc_address(self):
        """
        Get LTC address.
        :return:
        """
        return await self.get_crypto_address('get_ltc_address')

    async def get_eth_address(self):
        """
        GET ETH address.
        :return:
        """
        return await self.get_crypto_address('get_eth_address')

    async def get_crypto_address(self, action):
        """
        Get crypto address by action.
        :param action:
        :return:
        """
        params = {
            'wallet_id': self.wallet_id,
            'sign': await self.generate_wallet_signature(),
            'action': action,
        }

        return await self.send_request(params=params, url=self.wallet_api_url)

    async def get_btc_transaction(self, transaction_id):
        """
        Get information about BTC transaction.
        :param transaction_id:
        :return:
        """
        return await self.get_transaction('get_btc_transaction', transaction_id)

    async def get_ltc_transaction(self, transaction_id):
        """
        Get information about LTC transaction.
        :param transaction_id:
        :return:
        """
        return await self.get_transaction('get_ltc_transaction', transaction_id)

    async def get_eth_transaction(self, transaction_id):
        """
        Get information about ETH transaction.
        :param transaction_id:
        :return:
        """
        return await self.get_transaction('get_eth_transaction', transaction_id)

    async def get_transaction(self, action, transaction_id):
        """
        Get information about transaction by action.
        :param action:
        :param transaction_id:
        :return:
        """
        params = {
            'wallet_id': self.wallet_id,
            'transaction_id': transaction_id,
            'sign': await self.__make_hash(params=[
                self.wallet_id,
                transaction_id,
                self.wallet_api_key
            ]),
            'action': action,
        }

        return await self.send_request(params=params, url=self.wallet_api_url)

    async def generate_payment_link(self, order_id, summ, currency='rub',
                                    description='', language='ru') -> str:
        """
        Generate payment link for redirect user to Free-Kassa.com.
        :param order_id:
        :param summ:
        :param email:
        :param description:
        :return:
        """
        params = {
            'o': order_id,
            'oa': summ,
            's': await self.generate_form_signature(summ, order_id, currency),
            'm': self.merchant_id,
            'currency': currency,
            'lang': language,
            'pay': "PAY",
            'us_desc': description,
        }

        return self.base_form_url + "?" + urlencode(params)

    async def generate_api_signature(self):
        """
        Generate api signature
        :return:str
        """
        return hashlib.md5(
            str(self.merchant_id).encode('utf-8')
            + str(self.second_secret).encode('utf-8')).hexdigest()

    async def generate_wallet_signature(self):
        """
        Generate wallet signature
        :return:
        """
        return hashlib.md5(
            str(self.wallet_id + self.wallet_api_key).encode('utf-8'))\
            .hexdigest()

    async def generate_form_signature(self, amount, order_id, currency):
        """
        Generate signature for form and link
        :param amount:
        :param order_id:
        :return:
        """
        return await self.__make_hash(sep=":", params=[
            str(self.merchant_id),
            str(amount),
            str(self.first_secret),
            str(currency),
            str(order_id),
        ])

    async def __make_hash(self, params, sep=' '):
        """
        Generate hash query for request params
        :param params:
        :param sep:
        :param args:
        :param kwargs:
        :return:
        """
        sign = f'{sep}'.join(params)
        return hashlib.md5(sign.encode('utf-8')).hexdigest()
