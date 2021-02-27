
include common/Makefile.common


LATEST_BUILD_VERSION = $(shell ls -latr ./dist/*.tar.gz  | tail -n 1  | awk '{print $$9}' | cut -d / -f 3)
LATEST_BUILD_PATH = ./dist/$(LATEST_BUILD_VERSION)

# Virtualenv vars 
VIRTUALENV_NAME = jenkins_rapid_virtual_env
VIRTUALENVWRAPPER_PYTHON = $(shell which python3)
PIP_PACKAGE = jenkins_rapid


local-install: dev-install 
	 
test-build-pip-install: build_package test-pip-install test-jrp

test-build-clean-pip-install: build_package pip-clean test-pip-install test-jrp

test-jrp:
	. $(VIRTUALENV_NAME)/bin/activate \
		&&	jrp -v  

	

build-upload: build_package upload_pypi


init-jenkins-test-container:
	docker run -p 8080:8080 -v /home/sid/code/super_tmp/jenkins_home/jenkins_home:/var/jenkins_home jenkins/jenkins:lts 

test-run:
	. $(VIRTUALENV_NAME)/bin/activate \
		&& cd ./test/pipelines \
		&&	jrp -j test_jrp -f test_jenkinsfile  


