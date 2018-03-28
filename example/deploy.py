from pyinfra_prometheus import deploy_node_exporter, deploy_prometheus
SUDO = True

deploy_prometheus()
# These cannot be run straight after each other due to a know bug w.r.t user creation
# deploy_node_exporter()
