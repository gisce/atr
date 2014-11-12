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
    version='0.1.1',
    packages=find_packages(),
    url='http://git.gisce.lan/atr',
    license='MIT',
    install_requires=INSTALL_REQUIRES,
    entry_points="""
        [console_scripts]
        atr=atr.cli:atr
    """,
    author='GISCE-TI, S.L.',
    author_email='devel@gisce.net',
    description='ATR Utils'
)
