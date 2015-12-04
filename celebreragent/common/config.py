import uuid

from oslo_config import cfg
from oslo_config import types
from oslo_log import log as logging

from celebreragent import version

portType = types.Integer(1, 65535)

celebreragent_opts = [
    cfg.StrOpt('agent-uuid', default=str(uuid.uuid4()),
               help='Unique agent identification ')
]

CONF = cfg.CONF
CONF.register_cli_opts(celebreragent_opts)


def parse_args(args=None, usage=None, default_config_files=None):
    logging.register_options(CONF)
    logging.setup(CONF, 'celebreragent')
    CONF(args=args,
         project='celebreragent',
         version=version.version_string,
         usage=usage,
         default_config_files=default_config_files)
