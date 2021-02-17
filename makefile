
#

LATEST_BUILD_VERSION = $(shell ls -latr ./dist/*.tar.gz  | tail -n 1  | awk '{print $$9}' | cut -d / -f 3)
LATEST_BUILD_PATH = ./dist/$(LATEST_BUILD_VERSION)

build_package:
	python3.7 setup.py sdist 


upload_pypi:
	# 	pip3.7 install --user --upgrade twine
	twine upload $(LATEST_BUILD_PATH)  -u $(PYPI_USER) -p $(PYPI_PASS)

dev-install: 
	pip3 install -e ./ 


build-upload: build_package upload_pypi


run_jenkins_test:
	docker run -p 8080:8080 -v /home/sid/code/super_tmp/jenkins_home/jenkins_home:/var/jenkins_home jenkins:nbn_telemetry


