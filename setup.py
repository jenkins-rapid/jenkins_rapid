#!/usr/bin/env python

from setuptools import setup
import io

install_requires = [
    'docopts==0.6.1',
    'python-jenkins==1.7.0',
    'requests==2.25.1',
    'xmltodict==0.12.0',
    'Jinja2==2.11.2',
    'PyYAML==4.2b1',
    'halo==0.0.31'
]

test_requires = [
    'pytest',
] 


def long_description():
    with io.open('README.md', encoding='utf8') as f:
        return f.read()


setup(name='jenkins_rapid',
      version='0.4.5',
      description='A simple tool to rapidly create and debug jenkins pipelines',
      long_description=long_description(),
      long_description_content_type='text/markdown',
      author='Siddarth Vijapurapu',
      author_email='sidwho@gmail.com',
      url='https://github.com/sidja/jenkins_rapid',
      license='MIT',
      packages=['jenkins_rapid'],
      scripts=['jenkins_rapid/bin/jrp'],
       install_requires=install_requires,
      package_data={'jenkins_rapid': ['data/new_job_template.xml',
                    'data/templates/config_xml_parameter_template.yaml']
                    },
      classifiers=[
        'Intended Audience :: Developers',
        'Environment :: Console :: Curses',
        'Operating System :: POSIX',
        'Operating System :: Unix',
        'Operating System :: POSIX :: Linux',
        'Operating System :: MacOS',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Topic :: Terminals',        
        ],

      )