"""
google authenticaion and user info.


get authentication user from google
"""

import json
from flask_oauth import OAuth
from urllib3 import PoolManager
import certifi

GOOGLE_CLIENT_ID = '571919489560-p5itd3kcf1ileur7ih5bn07kc51ur21p.apps.googleusercontent.com'
GOOGLE_CLIENT_SECRET = 'ji3-Qsfziyj6ya0IdXUd6sGT'
REDIRECT_URI = '/oauth2callback'  # one of the Redirect URIs from Google APIs console

OAUTH = OAuth()

GOOGLE = OAUTH.remote_app(
    'google',
    base_url='https://www.google.com/accounts/',
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    request_token_url=None,
    request_token_params={'scope': 'https://www.googleapis.com/auth/userinfo.email',
                          'response_type': 'code'},
    access_token_url='https://accounts.google.com/o/oauth2/token',
    access_token_method='POST',
    access_token_params={'grant_type': 'authorization_code'},
    consumer_key=GOOGLE_CLIENT_ID,
    consumer_secret=GOOGLE_CLIENT_SECRET)

def get_user_info(access_token):
    """user info from google profile

    get user info from google

    Arguments:
        access_token  -- token from google

    Returns:
        json -- user info: email, name, etc.
    """

    http_pool = PoolManager(cert_reqs='CERT_REQUIRED', ca_certs=certifi.where())
    headers = {'Authorization': 'OAuth '+access_token}
    http_request = http_pool.request(
        'GET',
        'https://www.googleapis.com/oauth2/v1/userinfo',
        None,
        headers)
    return json.loads(http_request.data.decode('utf-8', 'strict'))
