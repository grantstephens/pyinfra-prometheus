from setuptools import find_packages, setup


if __name__ == '__main__':
    setup(
        version='1.0',
        name='pyinfra-prometheus',
        url='https://github.com/grantstephens/pyinfra-prometheus',
        description='Install & bootstrap prometheus clusters with pyinfra.',
        packages=find_packages(),
        install_requires=('pyinfra~=1.2'),
        include_package_data=True,
        license='MIT',
    )
