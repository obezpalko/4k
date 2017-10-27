from setuptools import setup

setup(
    name='e4',
    packages=['e4'],
    include_package_data=True,
    install_requires=[
        'flask',
        'sqlalchemy',
        'matplotlib'
    ],
    setup_requires=[
        'pytest-runner',
    ],
    tests_require=[
        'pytest',
    ],
)
