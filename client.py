import os

import oslo_messaging as messaging
import time
from oslo_messaging import rpc
from oslo_messaging import target
from oslo_config import cfg
from oslo_service import service

import uuid
import eventlet


CONF = cfg.CONF

CONF(project='test-client')

if os.name == 'nt':
    eventlet.monkey_patch(os=False)
else:
    eventlet.monkey_patch()


class TestEndpoint(object):

    @classmethod
    def collect_report(cls, _, component_name, binary_data):
        print "Component name: %s" % component_name
        print "Report length: %s" % len(binary_data)
        with open(
            'report-%s_%s.tar.gz' % (
                component_name, str(time.time())
            ), 'w'
        ) as f:
            f.write(binary_data.decode('base64'))


transport = messaging.get_transport(CONF)

server_target = target.Target('celebrer', 'reports', server=str(uuid.uuid4()))
server = messaging.get_rpc_server(transport, server_target, [TestEndpoint()],
                                  'eventlet')

launcher = service.ServiceLauncher(CONF)
launcher.launch_service(server)

client_target = target.Target('celebrer', 'discovery', fanout=True)
client = rpc.RPCClient(transport, client_target, timeout=300)

svc = {'glance': ['glance-api', 'glance-registry']}

for node in svc['glance']:
    client.call({}, 'start_coverage', service_name=node)

raw_input("Press any key to stop coverage")

for node in svc['glance']:
    client.call({}, 'stop_coverage', service_name=node,
                component_name='glance')

client.call({}, 'genreport_coverage', component_name='glance')
