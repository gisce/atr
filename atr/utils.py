import logging
import os

from erppeek import Client as PeekClient
from osconf import config_from_environment
from raven import Client
from raven.handlers.logging import SentryHandler
import sh

from atr import VERSION


logger = logging.getLogger('atr')


def setup_logging(logfile=None):
    log_config = config_from_environment('LOG')
    if log_config:
        logging.basicConfig(**log_config)
    logger = logging.getLogger('atr')
    if logfile:
        handler = logging.FileHandler(logfile)
        formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    sentry = Client()
    sentry.tags_context({'version': VERSION})
    sentry_handler = SentryHandler(sentry, level=logging.ERROR)
    logger.addHandler(sentry_handler)
    logger.debug('ATR Logging setup done')


def setup_git(git_dir):
    if not os.path.exists(git_dir):
        logger.info('Creating dir: %s' % git_dir)
        os.makedirs(git_dir)
    if os.path.exists(os.path.join(git_dir, '.git')):
        logger.error("This directory is already a git directory.")
    else:
        sh.cd(git_dir)
        git = sh.git
        logger.info("Initializing .git directory")
        git.init()


def setup_peek(**peek_config):
    config = config_from_environment(
        'PEEK', ['server', 'user', 'password', 'db'], **peek_config
    )
    logger.debug('Using peek config: %s' % config)
    return PeekClient(**config)