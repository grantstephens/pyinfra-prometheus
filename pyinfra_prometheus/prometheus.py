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
        'tar -xzf {{ host.data.prometheus_temp_filename }} -C {{ host.data.prometheus_install_dir }}',
        when=download_prometheus.changed,
    )

    files.link(
        state, host,
        {'Symlink prometheus to /usr/bin'},
        '{{ host.data.prometheus_bin_dir }}/prometheus',  # link
        '{{ host.data.prometheus_install_dir }}/{{ host.data.prometheus_version_name }}/prometheus',
    )



@deploy('Configure prometheus', data_defaults=DEFAULTS)
def configure_prometheus(state, host, enable_service=True):
    # Setup prometheus init
    generate_service = files.template(
        state, host,
        {'Upload the prometheus systemd unit file'},
        get_template_path('prometheus.service.j2'),
        '/etc/systemd/system/prometheus.service',
    )

    # Configure prometheus
    files.template(
        state, host,
        {'Upload the prometheus config file'},
        get_template_path('prometheus.yml.j2'),
        '/etc/default/prometheus.yml',
    )

    # Start (/enable) the prometheus service
    op_name = 'Ensure prometheus service is running'
    if enable_service:
        op_name = '{0} and enabled'.format(op_name)

    init.systemd(
        state, host,
        {op_name},
        'prometheus',
        restarted=True,
        enabled=enable_service,
        daemon_reload=generate_service.changed,
    )
