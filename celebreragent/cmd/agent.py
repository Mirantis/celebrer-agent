import os
import eventlet
import sys
import uuid
import yaml

import oslo_messaging as messaging
from oslo_messaging import target
from oslo_service import service
from oslo_config import cfg
from oslo_log import log as logging
from oslo_messaging import rpc


from celebreragent import version
from celebreragent.common import utils
from celebreragent.common.handler import CelebrerHandler

if os.name == 'nt':
    eventlet.monkey_patch(os=False)
else:
    eventlet.monkey_patch()

root = os.path.join(os.path.abspath(__file__), os.pardir, os.pardir)
if os.path.exists(os.path.join(root, 'celebreragent', '__init__.py')):
    sys.path.insert(0, root)


class CelebrerAgent(object):
    def __init__(self):
        self._CONF = cfg.CONF
        self._INSTANCE_ID = str(uuid.uuid4())
        self._ENDPOINTS = [CelebrerHandler(self)]

    def _prepare_rpc_service(self, rkey, endpoints):
        transport = messaging.get_transport(self._CONF)
        s_target = target.Target('celebrer', rkey, server=self._INSTANCE_ID,
                                 fanout=True)
        return messaging.get_rpc_server(transport, s_target, endpoints,
                                        'eventlet')

    def call_rpc(self, rkey, method, **kwargs):
        transport = messaging.get_transport(self._CONF)
        client_target = target.Target('celebrer', rkey)
        client = rpc.RPCClient(transport, client_target, timeout=15)
        client.call({}, method, **kwargs)

    def parse_args(self, args=None, usage=None, default_config_files=None):
        logging.register_options(self._CONF)
        logging.setup(self._CONF, 'celebrer')
        self._CONF(args=args,
                   project='celebrer',
                   version=version.version_info,
                   usage=usage,
                   default_config_files=default_config_files)

    def is_primary(self):
        astude = yaml.load(open('/etc/astute.yaml'))
        for node in astude['nodes']:
            if node['fqdn'] == astude['fqdn']:
                return node['role'] == 'primary-controller'

    def main(self):
        try:
            self.parse_args()

            logging.setup(self._CONF, 'celebrer-agent')
            launcher = service.ServiceLauncher(self._CONF)
            launcher.launch_service(self._prepare_rpc_service("discovery",
                                                              self._ENDPOINTS))
            if self.is_primary():
                launcher.launch_service(
                    self._prepare_rpc_service("collector", self._ENDPOINTS))

            for component in utils.detect_services().keys():
                launcher.launch_service(
                    self._prepare_rpc_service(component, self._ENDPOINTS))

            launcher.wait()
        except RuntimeError as e:
            sys.stderr.write("ERROR: %s\n" % e)
            sys.exit(1)


def main():
    ca = CelebrerAgent()
    ca.main()

if __name__ == "__main__":
    main()
