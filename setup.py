from setuptools import setup, find_packages

setup(
    name='odoo_automation', 
    version='13.0', 
    packages=find_packages(),
    install_requires=['Adafruit-Blinka', 'simple-pid', 'RPi.GPIO', 'Flask==1.1.2', 'numpy', 'OdooRPC', 'smbus2']
    )