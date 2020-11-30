#!/usr/bin/env python

import json,sys,os,traceback,ssl
from time import sleep
from docopt import docopt
import jenkins
import requests
import xml.etree.ElementTree
import atexit
from pathlib import Path

if (not os.environ.get('PYTHONHTTPSVERIFY', '') and
getattr(ssl, '_create_unverified_context', None)):
    os.environ['PYTHONHTTPSVERIFY'] = '0'
    ssl._create_default_https_context = ssl._create_unverified_context

class Job() :
    def __init__(self,arguments):
        self.arguments = arguments
        if os.environ.get('JENKINS_URL'):
            self.url = os.environ['JENKINS_URL']
        else: 
            self.url = arguments['--url']
        self.jenkinsfile = arguments['--file']
        self.job = arguments['--job']
        self.timer = int(arguments['--wait-timer'])
        self.sleep = int(arguments['--sleep'])
        if os.environ.get('JENKINS_USER'):
            self.jenkins_user = os.environ['JENKINS_USER']
        else:
            self.jenkins_user = arguments["--user"]
        if os.environ.get('JENKINS_PASSWORD'):
            self.jenkins_password = os.environ['JENKINS_PASSWORD']
        else:
            self.jenkins_password = arguments["--token"]
        if arguments['--parameters']:
            try:
                self.parameters = dict(u.split("=") for u in arguments['--parameters'].split(","))
            except ValueError:
                print ("Your parameters should be in key=value format separated by ; for multi value i.e. x=1,b=2")
                exit(1)
        else:
            self.parameters = False            
        self.config_dir = "./.config/{}".format(self.job)
        self.config_file = "config.xml"
        self.new_job_config_xml_template="data/new_job_template.xml"
        self.job_number = None
        self.brand_new_job = False
        self.finish_success_msg = 'Finished: SUCCESS'
        self.finish_failure_msg = 'Finished: FAILURE'

    def if_job_exits(self):
        server = jenkins.Jenkins(self.url, username=self.jenkins_user, password=self.jenkins_password)
        return server.get_job_name(self.job)

    def main(self):
        atexit.register(self.exit_handler)
        print (self.if_job_exits())
        if self.if_job_exits():
            # update_job()
            print('{:#^74}'.format('  Updating job:{}  '.format(self.job) ))
            print('##{:^70}##'.format('  1. Get existing config xml  '))    
            self.config_file_path = self.get_config_xml()
            print('##{:^70}##'.format(self.config_file_path))
            print('##{:^70}##'.format('  2. Update xml  '))
            self.update_job_config()
            print('##{:^70}##'.format('  3. Reconfigure/Upload config xml  '))
            self.upload_job_config()
            print('{:#^74}'.format('  Updating Finished  '))
        else:
            # create_job
            print('{:#^74}'.format('  Creating job:{}  '.format(self.job) ))
            print('##{:^70}##'.format('  1. Use template xml  '))
            print('##{:^70}##'.format('  2. Update template xml  '))
            self.create_new_config_xml()
            print('##{:^70}##'.format('  3. Create job with xml  '))
            self.create_new_job()
            print('{:#^74}'.format('  Finished creating job  '))
        if self.if_job_exits():
            self.get_crumb()
            queue_url = self.trigger_build()
            self.job_number = self.waiting_for_job_to_start(queue_url)
            self.console_output(self.job_number)

    def create_new_config_xml(self):
        # Create config folder 
        if not os.path.exists(self.config_dir):                                                                                                                                                                                    
            os.makedirs(self.config_dir)
        # Load config XML template
        new_job_config_xml_template_path = str(Path(__file__).parent / self.new_job_config_xml_template)
        et = xml.etree.ElementTree.parse(new_job_config_xml_template_path)
        xml_script = et.getroot().find('definition').find('script')
        #  Copy pipeline script file into config xml template  
        with open(self.jenkinsfile, 'r') as pipeline_file:
            xml_script.text = pipeline_file.read()
        # Write new xml config template
        et.write(self.config_dir+"/"+self.config_file)
        print('##{:70}##'.format(self.config_dir+"/"+self.config_file))

    def create_new_job(self):
        print('##{:^70}##'.format('  Creating new Jenkins job  '))
        server = jenkins.Jenkins(self.url, username=self.jenkins_user, password=self.jenkins_password)
        with open(self.config_dir+"/"+self.config_file, 'r') as file:
            xml_file = file.read()
        create_job = server.create_job(self.job,xml_file)
        self.brand_new_job = True
        return

    def get_config_xml(self):
        server = jenkins.Jenkins(self.url, username=self.jenkins_user, password=self.jenkins_password)
        job_xml = server.get_job_config(self.job)
        print('##{:^70}##'.format(self.config_file))
        # Create config folder 
        if not os.path.exists(self.config_dir):                                                                                                                                                                                    
            os.makedirs(self.config_dir)
        # Write config xml into folder path
        with open('{}/{}'.format(self.config_dir,self.config_file), 'w') as file:
            file.write(job_xml)
        config_file = '{}/{}'.format(self.config_dir,self.config_file)
        return config_file

    def update_job_config(self):
        print('##{:^70}##'.format('  Updating Config  '))
        server = jenkins.Jenkins(self.url, username=self.jenkins_user, password=self.jenkins_password)
        et = xml.etree.ElementTree.parse(self.config_file_path)
        xml_script = et.getroot().find('definition').find('script')
        with open(self.jenkinsfile, 'r') as pipeline_file:
            xml_script.text = pipeline_file.read()
            
        et.write(self.config_file_path)
        print('##{:^70}##'.format('  Finished updating config  '))
    
    def upload_job_config(self):
        print('##{:^70}##'.format('  Uploading Jenkins file and config  '))
        server = jenkins.Jenkins(self.url, username=self.jenkins_user, password=self.jenkins_password)
        with open(self.config_file_path, 'r') as file:
            xml_file = file.read()
        reconfigure_job_xml = server.reconfig_job(self.job,xml_file)
        print('##{:^70}##'.format('  Finished uploading  '))

    def get_crumb(self):
        if self.url:
            crumb_url=self.url+"/crumbIssuer/api/json"
            r = requests.get(crumb_url,auth=(self.jenkins_user, self.jenkins_password), verify=False)
            response = r.json()
            self.crumb=response["crumb"]
            print(response["crumb"]) 
        else:
            print("Check parameters")
            print("url parameter is missing")

    def trigger_build(self):
        headers = {
                "Jenkins-Crumb":self.crumb
        }
        # Do a build request
        if self.parameters and self.brand_new_job is not True:
            build_url = self.url + "/job/" + self.job + "/buildWithParameters"
            print("Triggering a build via post @ ", build_url)
            print("Params :", str(self.parameters))
            build_request = requests.post(build_url,params=self.parameters,auth=(self.jenkins_user, self.jenkins_password), verify=False,headers=headers)
        else:
            build_url = self.url + "/job/" + self.job + "/build"
            print("Triggering a build via get @ ", build_url)
            build_request = requests.post(build_url,auth=(self.jenkins_user, self.jenkins_password), verify=False,headers=headers)
            self.brand_new_job = False
        if build_request.status_code == 201:
            queue_url =  build_request.headers['location'] +  "api/json"
            print("Build is queued @ ", queue_url)
        else:
            print("Your build somehow failed")
            print(build_request.status_code)
            print(build_request.url)
            exit(1)
        return queue_url

    def waiting_for_job_to_start(self, queue_url):
        # Poll till we get job number
        print("\nStarting polling for our job to start")
        timer = self.timer
        waiting_for_job = True 
        while waiting_for_job:
            queue_request = requests.get(queue_url, auth=(self.jenkins_user, self.jenkins_password), verify=False)
            if queue_request.json().get("why") != None:
                print(" . Waiting for job to start because :", queue_request.json().get("why"))
                timer -= 1
                sleep(self.sleep)
            else:
                waiting_for_job = False
                job_number = queue_request.json().get("executable").get("number")  
                print(" Job is being build number: ", job_number  )
            if timer == 0:
                print(" time out waiting for job to start")
                exit(1)
        # Return the job numner 
        return job_number

    def console_output(self, job_number):
        print('#'*74)
        print('##{:^70}##'.format("   Jenkins logs    "))
        print('#'*74)
        headers = {
                "Jenkins-Crumb":self.crumb,
                "Content-type": "application/x-www-form-urlencoded; charset=UTF-8",
                "Content-Length": "10"
        }
        # Get job console till job stops
        job_url = self.url + "/job/" + self.job + "/" + str(job_number) + "/logText/progressiveText" 
        print(" Getting Console output @ ", job_url)
        start_at = 0
        stream_open = True
        check_job_status = 0
        console_requests_session = requests.session()
        console_requests_session.auth=(self.jenkins_user, self.jenkins_password)
        while stream_open:
            console_response = console_requests_session.post(job_url, data={'start': start_at }, verify=False,headers=headers)
            content_length = int(console_response.headers.get("Content-Length",-1))
            content_length = int("10")
            if console_response.status_code != 200:
                print(" Oppps we have an issue ... ")
                print(console_response.content)
                print(console_response.headers)
                exit(1)
            if content_length == 0:
                sleep(self.sleep)
                check_job_status +=1
            else:
                check_job_status = 0
                # Print to screen console
                if len(console_response.content) > 0:
                    if self.finish_failure_msg in str(console_response.content):
                        sleep(10)
                        print(self.finish_failure_msg)
                        print("Stopping jrp")
                        sys.exit()
                    elif self.finish_success_msg in str(console_response.content):
                        sleep(10)
                        print(self.finish_success_msg)
                        print("Stopping jrp")
                        sys.exit()
                    else:
                        print(console_response.content.decode("utf-8"))
                try:
                    sleep(self.sleep)
                except Exception:
                    pass
                start_at = int(console_response.headers.get("X-Text-Size"))
            # No content for a while lets check if job is still running
            if check_job_status > 1:
                job_status_url = self.url + "/job/" + self.job + "/" + str(job_number) + "/api/json"
                job_requests = console_requests_session.get(job_status_url, verify=False)
                job_bulding= job_requests.json().get("building")
                if not job_bulding:
                    # We are done
                    print("stream ended")
                    stream_open = False
                else:
                    # Job is still running
                    check_job_status = 0
    
    def stop_jobs(self):
        server = jenkins.Jenkins(self.url, username=self.jenkins_user, password=self.jenkins_password)
        # List running jobs
        if self.job_number is not None :
            print('#'*74)
            print('##{:^70}##'.format('  Stoping Job [ {} ] build No:[{}]  '.format(self.job,self.job_number)))
            builds = server.stop_build(self.job,self.job_number)
            print('#'*74)
        else:
            print("No build to stop")
        return
    
    def exit_handler(self):
        self.stop_jobs()
        
    def delete_job(self):
        server = jenkins.Jenkins(self.url, username=self.jenkins_user, password=self.jenkins_password)
        if self.job.split('_')[0].lower() == 'tmp':
            server.delete_job(self.job)
        else:
            print("#"*74)
            print('##{:^70}##'.format(" UNABLE TO DELETE JOB   "))
            print('##{30:70}##'.format((" Can only delete jobs with the prefix of 'Tmp_' or 'tmp_'    ")))
            print('##{:^70}##'.format((" Example : 'tmp_test_deployment_build_DEV'   ")))
            print("#"*74)
        return





    