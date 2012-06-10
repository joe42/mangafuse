# -*- coding: utf-8 -*-
'''
Created on 30.08.2011

@author: joe
'''
import setuptools
setuptools.setup(
    name = "CloudFusion",
    packages = setuptools.find_packages(),
    scripts = ['scripts/mangafuse'],
    include_package_data = True,
    install_requires = ['mechanize', 'nose', 'oauth', 'poster', 'simplejson'],
    version = "0.5.0",
    description = "manga file system for accessing online reader",
    author = "Johannes Müller",
    author_email = "quirksquarks@web.de",
    url = "https://github.com/joe42/CloudFusion",
    download_url = "https://github.com/joe42/cloudfusion.tgz",
    keywords = ["encoding", "i18n", "xml"],
    classifiers = [
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.6",
        "Development Status :: 4 - Beta",
        "Environment :: Other Environment",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "License :: Other/Proprietary License",
        "Operating System :: Linux",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Archiving :: Backup",
        "Topic :: System :: Filesystems",
        ],
    long_description = """\
	mangafuse lets you access your mangas from an online reader like any file on your desktop.
"""
)
