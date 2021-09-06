import json
import datetime
import logging
import random
import string
from json import JSONDecodeError

import jwt
import requests

logger = logging.getLogger(__name__)


class FlexiQuizAPI:
    BASE_URL = 'https://www.flexiquiz.com/api/v1/'
    API_KEY = '94e31cda1ec152ab4d19b82d6d96a014'
    SSO_SECRET = 'bWdXRU5pREsyNEQwK1pJTm1ENU0wREJ3ZEBZZE1PbE54amVnTlFJMWpZ'

    def api_call(self, url, data=False, params={}):
        headers = {'X-API-KEY': self.API_KEY}
        if data:
            logger.debug('Flexiquiz API POST: url:{}, data:{}'.format(url, data))
            r = requests.post(url, data, headers=headers)
        else:
            r = requests.get(url, params, headers=headers)
        logger.debug('Flexiquiz API response: {}'.format(r.text))
        if r.status_code == 200:
            try:
                r_dict = r.json()
                return r_dict
            except JSONDecodeError:
                return True
        else:
            return None

    def get_all_users(self):
        url = self.BASE_URL + '/users/'
        return self.api_call(url)

    def get_all_quizzes(self):
        url = self.BASE_URL + '/quizzes/'
        return self.api_call(url)

    def change_quiz_status(self, quiz_id, active):
        url = self.BASE_URL + '/quizzes/{}'.format(quiz_id)
        status = 'open' if active else 'closed'
        data = {'status': status}
        return self.api_call(url, data)

    def create_user(self, user):
        url = self.BASE_URL + '/users/'
        data = {
            'user_name': user.username,
            'password': self.random_password(),
            'first_name': user.first_name,
            'last_name': user.last_name,
            'user_type': 'respondent',
            'email_address': user.email,
            'suspended': False,
            'send_welcome_email': True
        }
        return self.api_call(url, data)

    def assign_quiz(self, flexiquiz_user_id, quiz_id):
        url = self.BASE_URL + '/users/{}/quizzes'.format(flexiquiz_user_id)
        data = {'quiz_id': quiz_id}
        return self.api_call(url, data)

    @staticmethod
    def random_password():
        chars = string.ascii_uppercase + string.ascii_lowercase + string.digits
        size = random.randint(8, 12)
        return ''.join(random.choice(chars) for x in range(size))

    @staticmethod
    def sso_token(user):
        header = {
            "alg": "HS256",
            "typ": "JWT"
        }
        payload = {
            "user_name": user.username,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(seconds=60)
        }
        token = jwt.encode(headers=header, payload=payload, key=FlexiQuizAPI.SSO_SECRET)
        return str(token, 'ascii')
