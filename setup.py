#!/usr/bin/env python

from setuptools import setup
import io

install_requires = [
    'docopts',
    'python-jenkins',
    'requests'
]

test_requires = [
    'pytest',
] 


def long_description():
    with io.open('README.md', encoding='utf8') as f:
        return f.read()


setup(name='jenkins_rapid',
      version='0.3.10',
      description='A simple tool to rapidly create and debug jenkins pipelines',
      long_description=long_description(),
      long_description_content_type='text/markdown',
      author='Siddarth Vijapurapu',
      license='MIT',
      packages=['jenkins_rapid'],
      scripts=['jenkins_rapid/bin/jrp'],
       install_requires=install_requires,
      package_data={'jenkins_rapid': ['data/new_job_template.xml']},
      classifiers=[
        'Intended Audience :: End Users/Desktop',
        'Environment :: Console :: Curses',
        'Operating System :: POSIX',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.6',
        'Topic :: Terminals',        
        ],

      )