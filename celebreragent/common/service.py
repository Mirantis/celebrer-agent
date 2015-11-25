from __future__ import with_statement
import re
import os

EXEC_COMMAND_REGEX = r"exec start-stop-daemon (.*?) -- (.*?)end script"
SERVICE_DESCRIPTION_REGEX = r'description \"([^\"]+)\"'
SERVICE_PARAM_REGEX = r"--([\S]+)\s*([^\-][\S]+)?"


class Service:
    def __init__(self, startup_config):
        self.service_params = None
        self.service_args = None
        self.service_description = None
        self.service_name = os.path.basename(startup_config)

        with open(startup_config) as config:
            self.parse_config(config.read())

    def parse_config(self, config):
        config = re.sub(r"(\s*\\\n\s*)", " ", config)

        exec_command = re.search(EXEC_COMMAND_REGEX, config, re.I | re.S | re.M)
        service_description = re.search(SERVICE_DESCRIPTION_REGEX, config, re.I | re.S)

        if service_description:
            self.service_description = service_description.groups()[0]

        if exec_command:
            daemon_param_string, args = exec_command.groups()

            daemon_params = re.findall(
                SERVICE_PARAM_REGEX,
                re.sub(r"(\s+|\s*\\\n\s*)", " ", daemon_param_string)
            )

            self.service_params = {param: value for param, value in daemon_params}
            self.service_args = re.sub(r"(\s+|\s*\\\n\s*)", " ", args)
