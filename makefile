
#


build_package:
	python3.7 setup.py sdist 


upload_pypi:
	# 	pip3.7 install --user --upgrade twine
	twine upload dist/jenkins_rapid-*

dev-install: 
	pip3 install -e ./  
