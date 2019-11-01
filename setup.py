# -*- coding: utf-8 -*-

# Learn more: https://github.com/kennethreitz/setup.py

from setuptools import setup, find_packages


with open('README.rst') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='AutoFileUploader',
    version='1.0.0',
    description='Upload files of a specific directory to a server or OTA capable device via WiFi.',
    long_description=readme,
    author='Jonas Scharpf',
    author_email='jonas@brainelectronics.de',
    url='https://github.com/brainelectronics/AutoFileUploader',
    license=license,
    packages=find_packages(exclude=('tests', 'docs'))
)

