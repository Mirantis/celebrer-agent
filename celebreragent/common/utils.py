import base64
import commands
import json
import os

from . import service


def detect_services():

    def _load_components_from_json(path):
        enabled_components = []
        with open(path) as json_file:
            json_data = json.load(json_file)
        for item in json_data.keys():
            if json_data[item]:
                enabled_components.append(item)
        return enabled_components

    def _module_location():
        return os.path.dirname(os.path.abspath(service.__file__))

    service_map = {}
    for startup_file in [some_file for some_file in os.listdir("/etc/init/")
                         if some_file.endswith(".conf")]:
        component = os.path.basename(startup_file).split("-")[0]
        if component in _load_components_from_json(
                '%s/../etc/supported_components.json' % _module_location()):
            if component not in service_map.keys():
                service_map[component] = []
            service_map[component].append(
                service.Service(os.path.join("/etc/init", startup_file)))

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


def coverage_bin():
    for command in ['python-coverage', 'coverage']:
        if not commands.getstatusoutput(command)[0]:
            return command
        return None