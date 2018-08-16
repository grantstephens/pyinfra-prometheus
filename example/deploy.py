from pyinfra_prometheus import deploy_exporter, deploy_node_exporter, deploy_prometheus

SUDO = True

# Prometheus Example
# deploy_prometheus(extra_args='--web.enable-lifecycle')

# Node exporter example
# These cannot be run straight after each other due to a know bug w.r.t user creation
# deploy_node_exporter()

# Generic Node Exporter Example
deploy_exporter(
   # 'https://github.com/kbudde/rabbitmq_exporter/'
   # 'releases/download/v0.26.0/rabbitmq_exporter-0.26.0.linux-amd64.tar.gz',
   # 'https://github.com/prometheus/memcached_exporter/'
   # 'releases/download/v0.4.1/memcached_exporter-0.4.1.linux-amd64.tar.gz',
   'https://github.com/oliver006/redis_exporter/'
    'releases/download/v0.19.1/redis_exporter-v0.19.1.linux-amd64.tar.gz',
   extra_args='',
)
