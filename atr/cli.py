import logging
import os
from uuid import uuid1

import click

from atr import VERSION, tasks
from atr.utils import setup_logging, setup_git


@click.group()
@click.option('--log-level', default='INFO')
def atr(log_level):
    os.environ['LOG_LEVEL'] = log_level.upper()
    setup_logging()
    logger = logging.getLogger('atr')
    logger.info('Running atr version: %s' % VERSION)


@atr.command()
@click.option('--path', type=click.Path())
def init(path):
    setup_git(path)


@atr.command()
@click.option('--path', type=click.Path())
def import_xmls(path):
    input = tasks.gen_new_files_dir(path)
    output = '/tmp/switching/proc-xml-%s' % uuid1()
    tasks.sort_xmls(input, output)
    tasks.import_files(output)


@atr.command()
@click.option('--path', type=click.Path())
def retry(path):
    tasks.retry_import_files(path)


if __name__ == '__main__':
    atr()


