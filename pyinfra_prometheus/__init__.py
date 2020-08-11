# pyinfra prometheus
# File: pyinfra_prometheus/__init__.py
# Desc: export deploys and install/configure helper function

from pyinfra.api import deploy

from .generic_exporter import configure_exporter, install_exporter
from .node_exporter import configure_node_exporter, install_node_exporter
from .prometheus import configure_prometheus, install_prometheus


@deploy('Deploy prometheus')
def deploy_prometheus(
    enable_service=True,
    extra_args=None,
    state=None,
    host=None,
):
    install_prometheus(state=state, host=host)
    configure_prometheus(
        enable_service=enable_service,
        extra_args=extra_args,
        state=state,
        host=host,
    )


@deploy('Deploy the node exporter')
def deploy_node_exporter(
    enable_service=True,
    extra_args=None,
    state=None,
    host=None,
):
    install_node_exporter(state=state, host=host)
    configure_node_exporter(
        enable_service=enable_service,
        extra_args=extra_args,
        state=state,
        host=host,
    )


@deploy('Deploy an exporter')
def deploy_exporter(
    ex_url,
    enable_service=True,
    extra_args=None,
    state=None,
    host=None,
):
    install_exporter(ex_url, state=state, host=host)
    configure_exporter(
        ex_url,
        enable_service=enable_service,
        extra_args=extra_args,
        state=state,
        host=host,
    )
