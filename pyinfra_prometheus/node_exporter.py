# pyinfra node_exporter
# File: pyinfra_prometheus/node_exporter.py
# Desc: installs/configures node_exporter as a systemd service using pyinfra

from pyinfra.api import deploy, DeployError
from pyinfra.modules import files, init, server

from .defaults import DEFAULTS
from .util import get_template_path


@deploy('Install node_exporter', data_defaults=DEFAULTS)
def install_node_exporter(state, host):
    if not host.data.node_exporter_version:
        raise DeployError(
            'No node_exporter_version set for this host, refusing to install node_exporter!',
        )

    server.user(
        state, host,
        {'Create the node_exporter user (Called prometheus by default)'},
        '{{ host.data.node_exporter_user }}',
        shell='/sbin/nologin',
    )

    files.directory(
        state, host,
        {'Ensure the node_exporter install directory exists'},
        '{{ host.data.node_exporter_install_dir }}',
        user=host.data.node_exporter_user,
        group=host.data.node_exporter_user,
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
        state, host,
        {'Download node_exporter'},
        (
            '{{ host.data.node_exporter_download_base_url }}/'
            'v{{ host.data.node_exporter_version }}/'
            '{{ host.data.node_exporter_version_name }}.tar.gz'
        ),
        '{{ host.data.node_exporter_temp_filename }}',
    )

    # If we downloaded node_exporter, extract it!
    server.shell(
        state, host,
        {'Extract node_exporter'},
        'tar -xzf {{ host.data.node_exporter_temp_filename }}'
        ' -C {{ host.data.node_exporter_install_dir }}',
        when=download_node_exporter.changed,
    )

    files.link(
        state, host,
        {'Symlink node_exporter to /usr/bin'},
        '{{ host.data.node_exporter_bin_dir }}/node_exporter',  # link
        '{{ host.data.node_exporter_install_dir }}/'
        '{{ host.data.node_exporter_version_name }}/node_exporter',
    )


@deploy('Configure node_exporter', data_defaults=DEFAULTS)
def configure_node_exporter(state, host, enable_service=True, extra_args=None):

    op_name = 'Ensure node_exporter service is running'
    if enable_service:
        op_name = '{0} and enabled'.format(op_name)

    if host.fact.linux_distribution['major'] >= 16:
        # Setup node_exporter init
        generate_service = files.template(
            state, host,
            {'Upload the node_exporter systemd unit file'},
            get_template_path('node_exporter.service.j2'),
            '/etc/systemd/system/node_exporter.service',
            extra_args=extra_args,
        )

        init.systemd(
            state, host,
            {op_name},
            'node_exporter',
            running=True,
            restarted=generate_service.changed,
            daemon_reload=generate_service.changed,
            enabled=enable_service,
        )

    elif host.fact.linux_distribution['major'] == 14:
        generate_service = files.template(
            state, host,
            {'Upload the node_exporter init.d file'},
            get_template_path('init.d.j2'),
            '/etc/init.d/node_exporter',
            mode=755,
            ex_name='node_exporter',
            ex_bin_dir=host.data.node_exporter_bin_dir,
            ex_user=host.data.node_exporter_user,
            extra_args=extra_args,
        )
        # Start (/enable) the prometheus service
        init.d(
            state, host,
            {op_name},
            'node_exporter',
            running=True,
            restarted=generate_service.changed,
            reloaded=generate_service.changed,
            enabled=enable_service,
        )
