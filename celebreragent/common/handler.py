from __future__ import with_statement
import commands
import shutil
import tarfile
import time
import os

from . import utils


class CelebrerHandler(object):

    def __init__(self, agent):
        self.agent = agent

    def start_coverage(self, context, services):
        for service_name in services:
            component, service = self.agent.get_service(service_name)

            if service:
                commands.getoutput("service %s stop" % service_name)
                print "Service %s stoppped" % service_name

                cmd_run = "%s run --source=%s --parallel-mode %s &" % (
                    self.agent.get_coverage_exec(), component, "%s %s" % (
                        service.service_params['exec'],
                        service.service_args
                    )
                )

                cov_path = '/tmp/coverage_%s' % component

                if os.path.exists(cov_path):
                    shutil.rmtree(cov_path)

                os.mkdir(cov_path)
                utils.pushd(cov_path)

                print "RUN: %s" % cmd_run

                os.system(cmd_run)

                time.sleep(3)
                if service_name not in commands.getoutput("ps aux"):
                    commands.getoutput('service %s start' % service_name)
                    service_status = 'Failure'
                else:
                    service_status = 'Started'

                utils.popd()
                self.agent.call_rpc('reports', 'set_status',
                                    service_name=service_name,
                                    server_id=self.agent.get_instance_id(),
                                    status=service_status)

    def stop_coverage(self, context, services):
        for service_name in services:
            component, service = self.agent.get_service(service_name)

            os.system(
                'kill $(ps hf -C %s | grep "%s" | awk "{print \$1;exit}");' %
                (self.agent.get_coverage_exec(), service)
            )

            commands.getoutput('service %s start' % service)

            print "Service %s started" % service

            cov_path = '/tmp/coverage_%s' % component
            utils.combine(cov_path)

            if self.agent.is_primary():
                combine_path = '/tmp/coverage-combine_%s' % component
                if not os.path.exists(combine_path):
                    os.mkdir(combine_path)

                shutil.copyfile(
                    '%s/.coverage' % cov_path,
                    '%s/.coverage.%s' % (
                        combine_path,
                        self.agent.get_instance_id()
                    )
                )
                utils.combine(combine_path)
            else:
                with open('%s/.coverage' % cov_path) as binary_report:
                    # Send coverage report to primary controller
                    self.agent.call_rpc(
                        'collector', 'collect_coverage',
                        component_name=component,
                        binary_data=utils.prepare_data(
                            binary_report.read(), 'compress'
                        ),
                        node_uuid=self.agent.get_instance_id()
                    )
            self.agent.call_rpc('reports', 'set_status',
                                service_name=service_name,
                                server_id=self.agent.get_instance_id(),
                                status='Stopped')

    def collect_coverage(self, component_name, binary_data, node_uuid):
        combine_path = '/tmp/coverage-combine_%s' % component_name

        if not os.path.exists(combine_path):
            os.mkdir(combine_path)

        with open(
            '%s/.coverage.%s' % (combine_path, node_uuid), 'w'
        ) as binary_report:
            binary_report.write(utils.prepare_data(binary_data, 'decompress'))
        utils.combine(combine_path)

    def genreport_coverage(self, context, component_name):
        time.sleep(10)
        cov_path = '/tmp/coverage-combine_%s' % component_name
        report_file_name = "coverage_%s_%s.tar.gz" % (
            component_name,
            str(time.time())
        )

        utils.pushd(cov_path)

        commands.getoutput('%s xml --omit=*/openstack/*,*/tests/*' %
                           self.agent.get_coverage_exec())
        commands.getoutput('%s html --omit=*/openstack/*,*/tests/*' %
                           self.agent.get_coverage_exec())
        commands.getoutput('%s report --omit=*/openstack/*,*/tests/* -m > '
                           'report_%s.txt' % (self.agent.get_coverage_exec(),
                                              component_name))

        tar_file = tarfile.open(report_file_name, 'w:gz')
        file_list = os.listdir(cov_path)
        for file_name in file_list:
            tar_file.add(file_name)
        tar_file.close()

        # Upload report
        with open(report_file_name) as binary_report:
            self.agent.call_rpc(
                'reports', 'collect_report',
                component_name=component_name,
                binary_data=binary_report.read().encode('base64')
            )
        utils.popd()
        shutil.rmtree(cov_path)
