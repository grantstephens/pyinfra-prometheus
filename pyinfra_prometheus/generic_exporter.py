# pyinfra node_exporter
# File: pyinfra_prometheus/node_exporter.py
# Desc: installs/configures node_exporter as a systemd service using pyinfra

from pyinfra.api import deploy, DeployError
from pyinfra.modules import files, init, server

from .defaults import DEFAULTS
from .util import get_template_path


def _get_names(ex_url):
    ex_name = ex_url.split('/')[-1].split('.tar.gz')[0]
    ex_bin_name = ex_name.split('-')[0]
    return ex_name, ex_bin_name


@deploy('Install an exporter', data_defaults=DEFAULTS)
def install_exporter(
    state, host, ex_url,
    ex_install_dir=None,
    ex_user='prometheus',
    ex_bin_dir='/usr/local/bin',
):

    if ex_install_dir is None:
        ex_install_dir = '/usr/local'

    ex_name, ex_bin_name = _get_names(ex_url)

    server.user(
        state, host,
        {'Create the node_exporter user (Called prometheus by default)'},
        ex_user,
        shell='/sbin/nologin',
    )

    files.directory(
        state, host,
        {'Ensure the node_exporter install directory exists'},
        '{}/{}'.format(ex_install_dir, ex_name),
        user=host.data.node_exporter_user,
        group=host.data.node_exporter_user,
    )

    ex_temp_filename = state.get_temp_filename(
        ex_url,
    )

    download_exporter = files.download(
        state, host,
        {'Download exporter'},
        ex_url,
        ex_temp_filename,
    )

    # If we downloaded exporter, extract it!
    server.shell(
        state, host,
        {'Extract exporter'},
        'tar -xzf {} -C {}/'.format(ex_temp_filename, ex_install_dir),
        when=download_exporter.changed,
    )

    files.link(
        state, host,
        {'Symlink exporter to /usr/local/bin'},
        '{}/{}'.format(ex_bin_dir, ex_name),  # link
        '{}/{}/{}'.format(ex_install_dir, ex_name, ex_bin_name),
    )


@deploy('Configure exporter', data_defaults=DEFAULTS)
def configure_exporter(
    state, host, ex_url,
    ex_user='prometheus',
    ex_bin_dir='/usr/local/bin',
    enable_service=True,
    extra_args=None,
):
    ex_name, ex_bin_name = _get_names(ex_url)

    # Start (/enable) the node_exporter service
    op_name = 'Ensure exporter service is running'
    if enable_service:
        op_name = '{0} and enabled'.format(op_name)

    if host.fact.linux_distribution['major'] >= 16:
        # Setup node_exporter init
        generate_service = files.template(
            state, host,
            {'Upload the {} systemd unit file'.format(ex_name)},
            get_template_path('exporter.service.j2'),
            '/etc/systemd/system/{}.service'.format(ex_bin_name),
            ex_name=ex_name,
            ex_bin_dir=ex_bin_dir,
            ex_user=ex_user,
            extra_args=extra_args,
        )

        init.systemd(
            state, host,
            {op_name},
            ex_bin_name,
            running=True,
            restarted=generate_service.changed,
            reloaded=generate_service.changed,
            enabled=enable_service,
            daemon_reload=generate_service.changed,
        )

    elif host.fact.linux_distribution['major'] == 14:
        generate_service = files.template(
            state, host,
            {'Upload the {} init.d file'.format(ex_name)},
            get_template_path('init.d.j2'),
            '/etc/init.d/{}'.format(ex_name),
            mode=755,
            ex_name=ex_name,
            ex_bin_dir=ex_bin_dir,
            ex_user=ex_user,
            extra_args=extra_args,
        )

        # Start (/enable) the prometheus service
        init.d(
            state, host,
            {op_name},
            ex_name,
            running=True,
            restarted=generate_service.changed,
            reloaded=generate_service.changed,
            enabled=enable_service,
        )
