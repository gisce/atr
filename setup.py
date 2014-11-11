from setuptools import find_packages, setup

INSTALL_REQUIRES = [
    'erppeek',
    'sh',
    'click',
    'raven',
    'switching',
    'osconf'
]


setup(
    name='atr',
    version='0.1.0',
    packages=find_packages(),
    url='http://git.gisce.lan/atr',
    license='MIT',
    author='GISCE-TI, S.L.',
    author_email='devel@gisce.net',
    description='ATR Utils'
)
