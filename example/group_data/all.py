prometheus_version = '2.1.0'
node_exporter_version = '0.15.2'

prometheus_jobs = [
    {'prometheus': {
        'static_configs': {'targets': [
            'localhost:9090',
        ],
        },
    },
    },
]
