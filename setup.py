from setuptools import setup, find_packages

setup(
    name="your-package-name",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "nodriver",
        "websocket_client"
    ],
)