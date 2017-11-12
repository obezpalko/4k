from setuptools import setup
from e4 import __version__
setup(
    name='e4',
    version = __version__,
    packages=['e4'],
    include_package_data=True,
    install_requires=[
        'chardet',
        'requests',
        'flask',
        'flask_login',
        'google-api-python-client',
        'google-auth',
        'google-auth-oauthlib',
        'google-auth-httplib2',
        'flask_oauth',
        'URLEncoder',
        'sqlalchemy',
        'matplotlib',
        'uwsgi',
        'certifi',
        'urllib3'
    ],
    setup_requires=[
        'pytest-runner',
    ],
    tests_require=[
        'pytest',
    ],
)
