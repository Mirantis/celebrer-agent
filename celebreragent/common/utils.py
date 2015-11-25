import base64
import requests
import csv
import socket
import StringIO
import commands
import os

def detect_services():
    def ha_get_stats_url():
        return "http://%s:10000/;csv" % \
               commands.getoutput('cat /etc/hiera/globals.yaml | grep manage'
                                  'ment_vip | grep -E -o "([0-9]{1,3}[\.]){3'
                                  '}[0-9]{1,3}"')

    def ha_get_services(ha_stats_url):
        hostname = socket.gethostname().split(".")[0]
        data = requests.get(ha_stats_url).text.replace("#",'')
        svc = []
        f = StringIO.StringIO(data)
        reader = csv.reader(data.split('\n'), delimiter=',')
        for row in reader:
            if hostname in row:
                if '-' in row[0]:
                    svc.append(row[0].split("-")[0])
        return list(set(svc))

    def process_num(process):
        return commands.getoutput("ps aux | awk {' print $12'} | grep %s" %
                                  process).split("\n")

    def svc_add(svc_list, svc_name):
        if commands.getoutput("ps aux | grep %s | wc -l" % svc_name) > 1 and \
                        svc_name not in svc_list:
            svc_list.append(svc_name)
        return svc_list

    svc_list = ha_get_services(ha_get_stats_url())
    for service in ['nova', 'neutron']:
        svc_list = svc_add(svc_list, service)
    svc_dict = {}
    for item in svc_list:
        data = process_num(item)
        for item in data:
            if not "/" in item and not "-" in item:
                svc_key = item
                break
        svc_dict[svc_key] = list(set(data))
        svc_dict[svc_key].remove(svc_key)

    for item in svc_list:
        temp = []
        for subitem in svc_dict[item]:
            temp.append(subitem.split("/")[-1])
        svc_dict[item] = temp

    return svc_dict


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