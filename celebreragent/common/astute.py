from __future__ import with_statement
import yaml
import os

ASTUTE = {}

if os.path.exists("/etc/astute.yaml"):
    with open("/etc/astute.yaml") as astute_yaml:
        ASTUTE = yaml.load(astute_yaml)