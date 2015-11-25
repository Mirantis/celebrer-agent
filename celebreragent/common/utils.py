import base64
import commands
import os

from . import service

OS_COMPONENT_LIST = [
    "cinder",
    "glance",
    "heat",
    "keystone",
    "mistral",
    "murano",
    "neutron",
    "nova",
]


def detect_services():
    service_map = {}

    for startup_file in [ some_file for some_file in os.listdir("/etc/init/") if some_file.endswith(".conf") ]:
        component = os.path.basename(startup_file).split("-")[0]

        if component in OS_COMPONENT_LIST:
            if component not in service_map.keys():
                service_map[component] = []
            service_map[component].append(service.Service(os.path.join("/etc/init", startup_file)))

    return service_map


def prepare_data(data, method):
    if method == 'compress':
        return base64.b64encode(data.encode('zlib'))
    elif method == 'decompress':
        return base64.b64decode(data.decode('zlib'))


def combine(path):
    cwd = os.getcwd()
    os.chdir(path)
    commands.getoutput('python-coverage combine')
    os.chdir(cwd)