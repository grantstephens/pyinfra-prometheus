# pyinfra prometheus
# File: pyinfra_prometheus/prometheus.py
# Desc: installs/configures prometheus as a systemd service using pyinfra

from pyinfra.api import deploy, DeployError
from pyinfra.modules import files, init, server

from .defaults import DEFAULTS
from .util import get_template_path


@deploy('Install prometheus', data_defaults=DEFAULTS)
def install_prometheus(state, host):
    if not host.data.prometheus_version:
        raise DeployError(
            'No prometheus_version set for this host, refusing to install prometheus!',
        )

    server.user(
        name='Create the prometheus user',
        user='{{ host.data.prometheus_user }}',
        shell='/sbin/nologin',
        state=state,
        host=host,
    )

    files.directory(
        name='Ensure the prometheus data directory exists',
        path='{{ host.data.prometheus_data_dir }}',
        user=host.data.prometheus_user,
        group=host.data.prometheus_user,
        state=state,
        host=host,
    )

    files.directory(
        name='Ensure the prometheus install directory exists',
        path='{{ host.data.prometheus_install_dir }}',
        user=host.data.prometheus_user,
        group=host.data.prometheus_user,
        state=state,
        host=host,
    )

    # Work out the filename
    host.data.prometheus_version_name = (
        'prometheus-{0}.linux-'
        'amd64' if host.fact.arch == 'x86_64' else host.fact.arch
    ).format(host.data.prometheus_version)

    host.data.prometheus_temp_filename = state.get_temp_filename(
        'prometheus-{0}'.format(host.data.prometheus_version),
    )

    download_prometheus = files.download(
        name='Download prometheus',
        src=(
            '{{ host.data.prometheus_download_base_url }}/'
            'v{{ host.data.prometheus_version }}/'
            '{{ host.data.prometheus_version_name }}.tar.gz'
        ),
        dest='{{ host.data.prometheus_temp_filename }}',
        state=state,
        host=host,
    )

    # If we downloaded prometheus, extract it!
    if download_prometheus.changed:
        server.shell(
            name='Extract prometheus',
            commands='tar -xzf {{ host.data.prometheus_temp_filename }}'
            ' -C {{ host.data.prometheus_install_dir }}',
            state=state,
            host=host,
        )

    files.link(
        name='Symlink prometheus to /usr/bin',
        path='{{ host.data.prometheus_bin_dir }}/prometheus',  # link
        target='{{ host.data.prometheus_install_dir }}/{{ host.data.prometheus_version_name }}/prometheus',
        state=state,
        host=host,
    )


@deploy('Configure prometheus', data_defaults=DEFAULTS)
def configure_prometheus(state, host, enable_service=True, extra_args=None):
    # Configure prometheus
    generate_config = files.template(
        name='Upload the prometheus config file',
        src=get_template_path('prometheus.yml.j2'),
        dest='/etc/default/prometheus.yml',
        state=state,
        host=host,
    )
    op_name = 'Ensure prometheus service is running'
    if enable_service:
        op_name = '{0} and enabled'.format(op_name)
        restart = generate_config.changed

    if extra_args and ('--web.enable-lifecycle' in extra_args):
        restart = False
        hit_reload_endpoint = True
    else:
        hit_reload_endpoint = False
    # Setup prometheus init
    if host.fact.linux_distribution['major'] >= 16:
        generate_service = files.template(
            name='Upload the prometheus systemd unit file',
            src=get_template_path('prometheus.service.j2'),
            dest='/etc/systemd/system/prometheus.service',
            extra_args=extra_args,
            state=state,
            host=host,
        )
        # Start (/enable) the prometheus service
        init.systemd(
            name=op_name,
            service='prometheus',
            running=True,
            restarted=restart,
            enabled=enable_service,
            daemon_reload=generate_service.changed,
            state=state,
            host=host,
        )
        # This has to happen after the service reload
        if hit_reload_endpoint:
            server.shell(
                commands='curl -X POST http://localhost:9090/-/reload',
                state=state,
                host=host,
            )

    elif host.fact.linux_distribution['major'] == 14:
        generate_service = files.template(
            name='Upload the prometheus init.d file',
            src=get_template_path('init.d.j2'),
            dest='/etc/init.d/prometheus',
            extra_args=extra_args,
            state=state,
            host=host,
        )
        # Start (/enable) the prometheus service
        init.d(
            name=op_name,
            service='prometheus',
            running=True,
            restarted=restart,
            reloaded=generate_service.changed,
            enabled=enable_service,
            state=state,
            host=host,
        )
