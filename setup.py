from setuptools import find_packages, setup


if __name__ == '__main__':
    setup(
        version='0.1',
        name='pyinfra-prometheus',
        description='Install & bootstrap prometheus clusters with pyinfra.',
        packages=find_packages(),
        install_requires=('pyinfra>=0.5'),
        include_package_data=True,
    )
