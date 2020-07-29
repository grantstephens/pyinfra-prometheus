# pyinfra node_exporter
# File: pyinfra_prometheus/node_exporter.py
# Desc: installs/configures node_exporter as a systemd service using pyinfra

from pyinfra.api import deploy
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
        name='Create the node_exporter user (Called prometheus by default)',
        user=ex_user,
        shell='/sbin/nologin',
        state=state,
        host=host,
    )

    files.directory(
        name='Ensure the node_exporter install directory exists',
        path='{}/{}'.format(ex_install_dir, ex_name),
        user=host.data.node_exporter_user,
        group=host.data.node_exporter_user,
        state=state,
        host=host,
    )

    ex_temp_filename = state.get_temp_filename(
        ex_url,
    )

    download_exporter = files.download(
        name='Download exporter',
        src=ex_url,
        dest=ex_temp_filename,
        state=state,
        host=host,
    )

    # If we downloaded exporter, extract it!
    if download_exporter.changed:
        server.shell(
            name='Extract exporter',
            commands='tar -xzf {} -C {}/'.format(ex_temp_filename, ex_install_dir),
            state=state,
            host=host,
        )

    files.link(
        name='Symlink exporter to /usr/local/bin',
        path='{}/{}'.format(ex_bin_dir, ex_name),  # link
        target='{}/{}/{}'.format(ex_install_dir, ex_name, ex_bin_name),
        state=state,
        host=host,
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
            name='Upload the {} systemd unit file'.format(ex_name),
            src=get_template_path('exporter.service.j2'),
            dest='/etc/systemd/system/{}.service'.format(ex_bin_name),
            ex_name=ex_name,
            ex_bin_dir=ex_bin_dir,
            ex_user=ex_user,
            extra_args=extra_args,
            state=state,
            host=host,
        )

        init.systemd(
            name=op_name,
            service=ex_bin_name,
            running=True,
            restarted=generate_service.changed,
            reloaded=generate_service.changed,
            enabled=enable_service,
            daemon_reload=generate_service.changed,
            state=state,
            host=host,
        )

    elif host.fact.linux_distribution['major'] == 14:
        generate_service = files.template(
            name='Upload the {} init.d file'.format(ex_name),
            src=get_template_path('init.d.j2'),
            dest='/etc/init.d/{}'.format(ex_name),
            mode=755,
            ex_name=ex_name,
            ex_bin_dir=ex_bin_dir,
            ex_user=ex_user,
            extra_args=extra_args,
            state=state,
            host=host,
        )

        # Start (/enable) the prometheus service
        init.d(
            name=op_name,
            service=ex_name,
            running=True,
            restarted=generate_service.changed,
            reloaded=generate_service.changed,
            enabled=enable_service,
            state=state,
            host=host,
        )
