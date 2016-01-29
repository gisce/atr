from datetime import datetime
import logging
import re
import os
import shutil
from uuid import uuid1
import xmlrpclib

import sh
from raven import Client as SentryClient
from switching.input.messages import Message

from .utils import setup_peek


ACCEPTED_PROCESS = [
    'A3', 'B1', 'C1', 'C2', 'D1', 'M1'
]

TASKS_DIRS = [
    '_DONE',
    '_ERRORS',
    '_DISCARD'
]

sentry = SentryClient()
logger = logging.getLogger('atr')


def retry_import_files(input):
    errors = os.path.join(input, '_ERRORS')
    if not os.path.exists(errors):
        logger.error("Task dir _ERRORS doesn't exist.")
    for dir_name, dir_names, file_names in os.walk(errors):
        for file_name in file_names:
            error_path = os.path.join(dir_name, file_name)
            logger.info('Moving %s to %s' % (error_path, input))
            sh.mv(error_path, input)
    import_files(input)


def import_files(input):
    client = setup_peek()
    sw = client.GiscedataSwitching
    tasks_dirs = {}
    for td in TASKS_DIRS:
        td_path = os.path.join(input, td)
        tasks_dirs[td] = td_path
        if not os.path.exists(td_path):
            logger.debug('Creating tasks dir: %s' % td_path)
            os.mkdir(td_path)
    for dir_name, dir_names, file_names in os.walk(input):
        if dir_name in tasks_dirs.values():
            logger.debug('Skipping task_dir %s' % dir_name)
            continue
        logger.debug("Walking into directory %s" % dir_name)
        for file_name in sorted(file_names):
            logger.debug('File found: %s' % file_name)
            name, ext = os.path.splitext(file_name)
            if ext.upper() == '.XML':
                path = os.path.join(dir_name, file_name)
                with open(path, 'r') as xml_file:
                    xml = xml_file.read()
                    msg = Message(xml)
                    msg_tipus = 'XML type %s %s found' % (msg.tipus, file_name)
                    if msg.tipus not in ACCEPTED_PROCESS:
                        msg_tipus += ' (discarted)'
                        logger.info(msg_tipus)
                        sh.mv(path, tasks_dirs['_DISCARD'])
                    logger.info(msg_tipus)
                    try:
                        sw.importar_xml(xml, file_name)
                        sh.mv(path, tasks_dirs['_DONE'])
                        logger.info('XML {0} imported correctly'.format(
                            file_name
                        ))
                    except xmlrpclib.Fault as xml_fault:
                        error = str(xml_fault.faultCode).replace('\n', ' ')
                        logger.error('Error importing %s xml: %s (%s)' % (
                            msg.tipus, file_name, error),
                            extra={
                                'environ': os.environ,
                                'path': path
                            }
                        )
                        sh.mv(path, tasks_dirs['_ERRORS'])
                    except Exception:
                        sentry.captureException()
                        sh.mv(path, tasks_dirs['_ERRORS'])
    if not os.listdir(tasks_dirs['_ERRORS']):
        logger.info('Removing directory %s' % input)
        shutil.rmtree(input)


@sentry.capture_exceptions
def gen_new_files_dir(input, output=None):
    if not output:
        output = '/tmp/out-%s' % uuid1()
    logger.info('Output dir: %s' % output)
    if not os.path.exists(output):
        logger.debug('Creating output dir: %s' % output)
        os.makedirs(output)
    new_files = get_new_files(input)
    logger.info('%s new files found' % len(new_files))
    for n_file in new_files:
        try:
            dest = os.path.join(output, os.path.dirname(n_file))
            logger.info('Copying %s -> %s' % (n_file, dest))
            sh.cp('-R', n_file, dest)
            logger.info('Adding to git %s' % n_file)
            sh.git.add(n_file)
            sh.git.commit('-m', 'Added %s' % n_file)
        except:
            logger.error('File {0} not processed'.format(n_file))

    return output


@sentry.capture_exceptions
def get_new_files(input):
    sh.cd(input)
    git = sh.git
    return [
        x[3:].rstrip('\n') for x in git.status('--porcelain')
            if x.startswith('?? ')
    ]


@sentry.capture_exceptions
def sort_xmls(input, output):
    n_files = 0
    start = datetime.now()
    if not os.path.exists(output):
        os.makedirs(output)
    for dir_name, dir_names, file_names in os.walk(input):
        logger.debug("Walking into directory %s" % dir_name)
        for file_name in file_names:
            logger.debug('File found: %s' % file_name)
            name, ext = os.path.splitext(file_name)
            if ext.upper() == '.XML':
                path = os.path.join(dir_name, file_name)
                with open(path, 'r') as xml_file:
                    xml = xml_file.read(500)
                    cod = re.findall(
                        '<CodigoDeSolicitud>(.*)</CodigoDeSolicitud>', xml
                    )
                    step = re.findall(
                        '<CodigoDePaso>(.*)</CodigoDePaso>', xml
                    )
                if step:
                    step = step[0]
                else:
                    step = '00'
                if cod:
                    cod = cod[0]
                    logger.debug('CodigoDeProceso: %s CodigoDePaso: %s' % (
                        cod, step
                    ))
                    new_path = os.path.join(output, '%s-%s-%s' % (
                        cod, step, file_name)
                    )
                    old_path = os.path.join(dir_name, file_name)
                    logger.debug('XML Found: %s => %s' % (old_path, new_path))
                    shutil.copy(path, new_path)
                    n_files += 1
    logger.info('Sorted %s XML files in %s' % (n_files, datetime.now() - start))
