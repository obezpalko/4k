from setuptools import setup
from e4 import __version__
setup(
    name='e4',
    version = __version__,
    packages=['e4'],
    include_package_data=True,
    install_requires=[
        'flask',
        'sqlalchemy',
        'matplotlib',
        'gunicorn'
    ],
    setup_requires=[
        'pytest-runner',
    ],
    tests_require=[
        'pytest',
    ],
)
