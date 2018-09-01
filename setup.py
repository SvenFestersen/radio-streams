#!/usr/bin/env python
# -*- coding: utf-8 -*-
import setuptools

print(setuptools.find_packages("src"))

setuptools.setup(name="radiostreams",
                 version="0.1",
                 description="Audio streaming proxy.",
                 author='Sven Festersen',
                 package_dir={"":"src"},
                 packages=setuptools.find_packages("src"),
                 install_requires=["tornado >=5.0", "pycurl >=7.0"],
                 scripts=["scripts/stream-proxy"])