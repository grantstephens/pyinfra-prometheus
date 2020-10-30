# pyinfra node_exporter
# File: pyinfra_prometheus/node_exporter.py
# Desc: installs/configures node_exporter as a systemd service using pyinfra

from pyinfra.api import deploy, DeployError
from pyinfra.operations import files, server, systemd

from .defaults import DEFAULTS
from .util import get_template_path


@deploy('Install node_exporter', data_defaults=DEFAULTS)
def install_node_exporter(state=None, host=None):
    if not host.data.node_exporter_version:
        raise DeployError(
            'No node_exporter_version set for this host, refusing to install node_exporter!',
        )

    server.user(
        name='Create the node_exporter user (Called prometheus by default)',
        user='{{ host.data.node_exporter_user }}',
        shell='/sbin/nologin',
        state=state,
        host=host,
    )

    files.directory(
        name='Ensure the node_exporter install directory exists',
        path='{{ host.data.node_exporter_install_dir }}',
        user=host.data.node_exporter_user,
        group=host.data.node_exporter_user,
        state=state,
        host=host,
    )

    # Work out the filename
    host.data.node_exporter_version_name = (
        'node_exporter-{0}.linux-'
        'amd64' if host.fact.arch == 'x86_64' else host.fact.arch
    ).format(host.data.node_exporter_version)

    host.data.node_exporter_temp_filename = state.get_temp_filename(
        'node_exporter-{0}'.format(host.data.node_exporter_version),
    )

    download_node_exporter = files.download(
        name='Download node_exporter',
        src=(
            '{{ host.data.node_exporter_download_base_url }}/'
            'v{{ host.data.node_exporter_version }}/'
            '{{ host.data.node_exporter_version_name }}.tar.gz'
        ),
        dest='{{ host.data.node_exporter_temp_filename }}',
        state=state,
        host=host,
    )

    # If we downloaded node_exporter, extract it!
    if download_node_exporter.changed:
        server.shell(
            name='Extract node_exporter',
            commands='tar -xzf {{ host.data.node_exporter_temp_filename }}'
            ' -C {{ host.data.node_exporter_install_dir }}',
            state=state,
            host=host,
        )

    files.link(
        name='Symlink node_exporter to /usr/bin',
        path='{{ host.data.node_exporter_bin_dir }}/node_exporter',  # link
        target='{{ host.data.node_exporter_install_dir }}/'
        '{{ host.data.node_exporter_version_name }}/node_exporter',
        state=state,
        host=host,
    )


@deploy('Configure node_exporter', data_defaults=DEFAULTS)
def configure_node_exporter(enable_service=True, extra_args=None, state=None, host=None):
    if isinstance(extra_args, list):
        extra_args = ' '.join(extra_args)

    op_name = 'Ensure node_exporter service is running'
    if enable_service:
        op_name = '{0} and enabled'.format(op_name)

    generate_service = files.template(
        name='Upload the node_exporter systemd unit file',
        src=get_template_path('node_exporter.service.j2'),
        dest='/etc/systemd/system/node_exporter.service',
        extra_args=extra_args,
        state=state,
        host=host,
    )

    systemd.service(
        name=op_name,
        service='node_exporter',
        running=True,
        restarted=generate_service.changed,
        daemon_reload=generate_service.changed,
        enabled=enable_service,
        state=state,
        host=host,
    )
