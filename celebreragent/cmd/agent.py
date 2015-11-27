import commands
import os
import eventlet
import sys
import uuid

import oslo_messaging as messaging
from oslo_messaging import target
from oslo_service import service
from oslo_config import cfg
from oslo_log import log as logging
from oslo_messaging import rpc


from celebreragent import version
from celebreragent.common import utils
from celebreragent.common.handler import CelebrerHandler
from celebreragent.common import astute

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
        self._SERVICES = utils.detect_services()
        self._LOG = logging.getLogger(__name__)
        try:
            self._COVERAGE_EXEC = self._check_coverage_utility()
        except EnvironmentError as ex:
            self._LOG.exception(ex)
            exit()

    def _check_coverage_utility(self):
        executable_path = utils.coverage_bin()
        if not executable_path:
            raise EnvironmentError("Not found coverage.py utility")
        return executable_path

    def _prepare_rpc_service(self, rkey, endpoints):
        transport = messaging.get_transport(self._CONF)
        s_target = target.Target(
            'celebrer', rkey,
            server=self.get_logger(),
            fanout=True
        )
        return messaging.get_rpc_server(
            transport, s_target, endpoints, 'eventlet'
        )

    def get_logger(self):
        return self._LOG

    def get_instance_id(self):
        return self._INSTANCE_ID

    def get_coverage_exec(self):
        return self._COVERAGE_EXEC

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
        if commands.getoutput('ip a | grep hapr-host'):
            return astute.ASTUTE.get('fqdn')
        for node in astute.ASTUTE.get('nodes', []):
            if node['fqdn'] == astute.ASTUTE.get('fqdn'):
                return node['role'] == 'primary-controller'

    def get_service(self, service_name):
        for component, service_list in self._SERVICES.items():
            for service in service_list:
                if service.service_name == service_name:
                    return component, service
        return None, None

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

            for component in self._SERVICES.keys():
                launcher.launch_service(
                    self._prepare_rpc_service(component, self._ENDPOINTS))

            self.call_rpc("discovery", "discover_services",
                          services={
                              component: svc.service_name for
                              component, svc in self._SERVICES.items()
                          },
                          node_uuid=self.get_instance_id())

            launcher.wait()
        except RuntimeError as e:
            sys.stderr.write("ERROR: %s\n" % e)
            sys.exit(1)


def main():
    ca = CelebrerAgent()
    ca.main()

if __name__ == "__main__":
    main()
