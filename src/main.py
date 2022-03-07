import os
import sys
import logging
import yaml
import argparse
import logging.config
from configparser import ConfigParser
from logging import config

from adapter import Adapter

CONST_VERSION = 'V1.0.0'

parser = argparse.ArgumentParser(description='报文上传程序')
parser.add_argument('--config', '-c', help='配置文件')
args = parser.parse_args()

configparser = ConfigParser()
if os.path.exists(args.config) is False:
    print("配置文件app.config不存在！请检查配置文件")
    sys.exit()
configparser.read(args.config, encoding='utf-8')


def GetResource(relative_path: str):
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


with open(GetResource('logging.yaml'), 'r', encoding='utf-8') as f:
    logging_config = yaml.load(f, Loader=yaml.FullLoader)
    for key, value in logging_config['handlers'].items():
        if value.get('filename'):
            logfile_path = os.path.join(configparser['general']['logsPtah'], value.get('filename')) if configparser['general']['logsPtah'] else os.path.join('logs', value.get('filename'))
            value['filename'] = logfile_path
            if not os.path.exists(os.path.dirname(logfile_path)):
                os.makedirs(os.path.dirname(logfile_path))
    config.dictConfig(logging_config)
logger = logging.getLogger('main.common')

if __name__ == '__main__':
    logger.info('Running...')

    github_url = configparser['github']['url']
    github_user = configparser['github']['user']
    github_proxy = configparser['github']['proxy']

    gitea_url = configparser['gitea']['url']
    gitea_mirror = configparser['gitea']['mirror']
    gitea_username = configparser['gitea']['username']
    gitea_password = configparser['gitea']['password']
    gitea_organization = configparser['gitea']['organization']
    gitea_timeout = configparser['gitea']['timeout']
    gitea_proxy = configparser['gitea']['proxy']
    gitea_private = configparser['gitea']['private']

    adapter = Adapter(gitea_url=gitea_url, github_url=github_url)
    if not adapter.Login(gitea_username=gitea_username, gitea_password=gitea_password, gitea_proxy=gitea_proxy):
        logger.error('Login gitea failed')
        sys.exit()
    adapter.Collect(github_user=github_user, github_proxy=github_proxy)
    adapter.Sync(gitea_organization=gitea_organization, gitea_mirror=gitea_mirror, gitea_private=gitea_private, gitea_timeout=int(gitea_timeout))

    logger.info('Run End...')