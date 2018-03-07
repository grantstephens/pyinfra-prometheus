# pyinfra prometheus
# File: pyinfra_prometheus/util.py
# Desc: general utilities!

from os import path


def get_template_path(template):
    return path.join(
        path.dirname(__file__),
        'templates',
        template,
    )
