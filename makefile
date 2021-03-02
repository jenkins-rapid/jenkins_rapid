
include common/Makefile.common


LATEST_BUILD_VERSION = $(shell ls -latr ./dist/*.tar.gz  | tail -n 1  | awk '{print $$9}' | cut -d / -f 3)
LATEST_BUILD_PATH = ./dist/$(LATEST_BUILD_VERSION)

# Virtualenv vars 
VIRTUALENV_NAME = jenkins_rapid_virtual_env
VIRTUALENVWRAPPER_PYTHON = $(shell which python3)
PIP_PACKAGE = jenkins_rapid

# JRP VARS
JENKINS_USER?=admin
JENKINS_PASSWORD?=admin
JENKINS_URL?=http://localhost:8080/




local-install: dev-install 
	 
test-build-pip-install: build_package test-pip-install test-jrp

test-build-clean-pip-install: build_package pip-clean test-pip-install test-jrp

test-jrp:
	. $(VIRTUALENV_NAME)/bin/activate \
		&&	jrp -v  

build-upload: build_package upload_pypi

test-run:
	. $(VIRTUALENV_NAME)/bin/activate \
		&& cd ./test/pipelines \
		&&	jrp -j test_jrp -f test_jenkinsfile  

test-jrp-create-local: local-install
	. $(VIRTUALENV_NAME)/bin/activate \
		&& cd ./test/pipelines \
		&&	jrp -j test_jrp -f test_jenkinsfile

test-jrp-create: 
	. $(VIRTUALENV_NAME)/bin/activate \
		&& cd ./test/pipelines \
		&&	jrp -j test_jrp -f test_jenkinsfile

test-jrp-update-with-params: 
	. $(VIRTUALENV_NAME)/bin/activate \
		&& cd ./test/pipelines \
		&&	jrp -j test_jrp -f test_jenkinsfile --parameters-yaml pipeline_params.yaml

test-jrp-create-with-params: 
	. $(VIRTUALENV_NAME)/bin/activate \
		&& cd ./test/pipelines \
		&&	jrp delete -j test_jrp \
		&&  jrp -j test_jrp -f test_jenkinsfile --parameters-yaml pipeline_params.yaml



clean-jrp-test-job:
	. $(VIRTUALENV_NAME)/bin/activate \
		&& cd ./test/pipelines \
		&&	jrp delete -j test_jrp 

test-jrp-build-create: build_package test-pip-install test-jrp-create

test-jrp-build-create-clean: build_package test-pip-install test-jrp-create clean-jrp-test-job

test-all: test-jrp-build-create-clean test-jrp-update-with-params test-jrp-create-with-params clean-jrp-test-job


## Docker

build-jenkins-test-container-plugins-installed:
	cd ./test; \
	docker build -t sidwho/jenkins_lite_install:2.222.4-lts-slim -f Dockerfile_plugins_installed .

build-jenkins-test-container-plugins-copied:
	cd ./test; \
	docker build -t sidwho/jenkins_full_install:2.222.4-lts-slim -f Dockerfile_plugins_copied .
	docker tag sidwho/jenkins_full_install:2.222.4-lts-slim sidwho/jenkins_built:regular_install_latest


init-jenkins-test-container:
# 	docker run -p 8080:8080 -v /home/sid/code/nbn/code/competencies/jenkins_rapid/test/jenkins_home_latest:/var/jenkins_home jenkins/jenkins:lts
# 	docker run -p 8080:8080 -v /home/sid/code/nbn/code/competencies/jenkins_rapid/test/jenkins_home_2.22.4:/var/jenkins_home jenkins/jenkins:2.222.4-lts-slim
	docker run -p 8080:8080 sidwho/jenkins_built:regular_install_latest 
