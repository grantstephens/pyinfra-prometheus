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
        state, host,
        {'Create the prometheus user'},
        '{{ host.data.prometheus_user }}',
        shell='/sbin/nologin',
    )

    files.directory(
        state, host,
        {'Ensure the prometheus data directory exists'},
        '{{ host.data.prometheus_data_dir }}',
        user=host.data.prometheus_user,
        group=host.data.prometheus_user,
    )

    files.directory(
        state, host,
        {'Ensure the prometheus install directory exists'},
        '{{ host.data.prometheus_install_dir }}',
        user=host.data.prometheus_user,
        group=host.data.prometheus_user,
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
        state, host,
        {'Download prometheus'},
        (
            '{{ host.data.prometheus_download_base_url }}/'
            'v{{ host.data.prometheus_version }}/'
            '{{ host.data.prometheus_version_name }}.tar.gz'
        ),
        '{{ host.data.prometheus_temp_filename }}',
    )

    # If we downloaded prometheus, extract it!
    server.shell(
        state, host,
        {'Extract prometheus'},
        'tar -xzf {{ host.data.prometheus_temp_filename }}'
        ' -C {{ host.data.prometheus_install_dir }}',
        when=download_prometheus.changed,
    )

    files.link(
        state, host,
        {'Symlink prometheus to /usr/bin'},
        '{{ host.data.prometheus_bin_dir }}/prometheus',  # link
        '{{ host.data.prometheus_install_dir }}/{{ host.data.prometheus_version_name }}/prometheus',
    )


@deploy('Configure prometheus', data_defaults=DEFAULTS)
def configure_prometheus(state, host, enable_service=True, extra_args=None):
    # Configure prometheus
    generate_config = files.template(
        state, host,
        {'Upload the prometheus config file'},
        get_template_path('prometheus.yml.j2'),
        '/etc/default/prometheus.yml',
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
            state, host,
            {'Upload the prometheus systemd unit file'},
            get_template_path('prometheus.service.j2'),
            '/etc/systemd/system/prometheus.service',
            extra_args=extra_args,
        )
        # Start (/enable) the prometheus service
        init.systemd(
            state, host,
            {op_name},
            'prometheus',
            running=True,
            restarted=restart,
            enabled=enable_service,
            daemon_reload=generate_service.changed,
        )
        # This has to happen after the service reload
        if hit_reload_endpoint:
            server.shell(
                state, host,
                'curl -X POST http://localhost:9090/-/reload',
            )

    elif host.fact.linux_distribution['major'] == 14:
        generate_service = files.template(
            state, host,
            {'Upload the prometheus init.d file'},
            get_template_path('init.d.j2'),
            '/etc/init.d/prometheus',
            extra_args=extra_args,
        )
        # Start (/enable) the prometheus service
        init.d(
            state, host,
            {op_name},
            'prometheus',
            running=True,
            restarted=restart,
            reloaded=generate_service.changed,
            enabled=enable_service,
        )
