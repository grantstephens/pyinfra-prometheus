# pyinfra prometheus
# File: pyinfra_prometheus/__init__.py
# Desc: export deploys and install/configure helper function

from pyinfra.api import deploy

from .generic_exporter import configure_exporter, install_exporter
from .node_exporter import configure_node_exporter, install_node_exporter
from .prometheus import configure_prometheus, install_prometheus


@deploy('Deploy prometheus')
def deploy_prometheus(state, host, enable_service=True, extra_args=None):
    install_prometheus(state, host)
    configure_prometheus(state, host, enable_service=enable_service, extra_args=extra_args)


@deploy('Deploy the node exporter')
def deploy_node_exporter(state, host, enable_service=True, extra_args=None):
    install_node_exporter(state, host)
    configure_node_exporter(state, host, enable_service=enable_service, extra_args=extra_args)


@deploy('Deploy an exporter')
def deploy_exporter(
    state, host, ex_url,
    enable_service=True,
    extra_args=None,
):
    install_exporter(state, host, ex_url)
    configure_exporter(state, host, ex_url, enable_service=enable_service, extra_args=extra_args)
