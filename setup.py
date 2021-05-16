from setuptools import setup

setup(
    name="tssb_cli",
    version='0.1',
    install_requires = [
        'docopt==0.6.2',
        'subprocess-tee==0.3.1'
    ],
    packages=['tssb_cli'],
)
