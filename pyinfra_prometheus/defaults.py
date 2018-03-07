# pyinfra prometheus
# File: pyinfra_prometheus/defaults.py
# Desc: default data for pyinfra prometheus

DEFAULTS = {
    # Install
    'prometheus_bin_dir': '/usr/local/bin',
    'prometheus_data_dir': '/var/lib/prometheus',
    'prometheus_download_base_url': 'https://github.com/prometheus/prometheus/releases/download/',
    'prometheus_evaluation_interval': '15s',
    'prometheus_install_dir': '/usr/local/prometheus',
    'prometheus_scrape_interval': '15s',
    'prometheus_user': 'prometheus',
    'prometheus_version': None,
    'prometheus_jobs': {
        'prometheus':{
            'static_configs':[
                'localhost:9090'
            ],
        },
        'nodes':{
            'static_configs':[
                'localhost:9100'
            ],
        },
    },

    'node_exporter_bin_dir': '/usr/local/bin',
    'node_exporter_download_base_url': 'https://github.com/prometheus/node_exporter/releases/download/',
    'node_exporter_install_dir': '/usr/local/node_exporter',
    'node_exporter_user': 'prometheus',
    'node_exporter_version': None,
}
