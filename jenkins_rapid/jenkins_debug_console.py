#!/usr/bin/env python

import json,sys,os,traceback,ssl
from time import sleep
from docopt import docopt
import jenkins
import requests
import xml.etree.ElementTree
import atexit
from pathlib import Path
from halo import Halo
import yaml
import xmltodict
from jinja2 import Template, Environment, FileSystemLoader
import xml.etree.ElementTree as ET


if (not os.environ.get('PYTHONHTTPSVERIFY', '') and
getattr(ssl, '_create_unverified_context', None)):
    os.environ['PYTHONHTTPSVERIFY'] = '0'
    ssl._create_default_https_context = ssl._create_unverified_context

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    RED = '\033[31m'
    OKCYAN = '\033[96m'
    BLUE = '\033[34m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class Job() :
    def __init__(self,arguments):
        self.crumb      = None
        self.build_url  = None         
        self.job_number = None
        self.job_status = None
        self.arguments  = arguments
        self.jenkinsfile = arguments['--file']
        self.spinner    = Halo(text='Building ..', spinner='dots')
        self.job    = arguments['--job']
        # self.timer  = int(arguments['--wait-timer'])
        # self.sleep  = int(arguments['--sleep'])
        self.timer  = 100
        self.sleep  = 2
        self.url    = os.environ.get('JENKINS_URL') if os.environ.get('JENKINS_URL') else arguments['--url']
        self.jenkins_user = os.environ.get('JENKINS_USER') if os.environ.get('JENKINS_USER') else arguments["--user"]
        self.jenkins_password = os.environ.get('JENKINS_PASSWORD') if os.environ.get('JENKINS_PASSWORD') else arguments["--token"]
        self.parametersfile =  arguments['--parameters-yaml']
        self.parameters     = True if arguments['--parameters-yaml'] else False
        self.brand_new_job  = False
        self.config_dir     = "./.config/{}".format(self.job)
        self.config_file    = "config.xml"
        self.new_job_config_xml_template="data/new_job_template.xml"
        self.template_folder_path="data/templates"
        self.params_yaml_template='config_xml_parameter_template.yaml'
        self.finish_success_msg = 'Finished: SUCCESS'
        self.finish_failure_msg = 'Finished: FAILURE'
        self.server = jenkins.Jenkins(self.url, username=self.jenkins_user, password=self.jenkins_password)

    def if_job_exits(self):
        return self.server.get_job_name(self.job)

    def validate_jenkinsfile(self):
        self.spinner.text ="Validating Jenkinsfile"
        sleep(0.05)
        files = {
            'jenkinsfile': [None, None],
        }
        validate_url = self.url + '/pipeline-model-converter/validate'
        try:
            with open(self.jenkinsfile, 'r') as pipeline_file:
                files['jenkinsfile'][1] = pipeline_file
                j_validate_response = requests.post(validate_url, files=files, auth=(self.jenkins_user, self.jenkins_password), verify=False)
            if "Errors encountered validating Jenkinsfile" in j_validate_response.text:
                self.spinner.text ="Validation Error ⚠️ !"
                sleep(0.05)
                print("\n\n"+j_validate_response.text)
                print(" To ignore jenkinsfile validation use -i flag\n\n")
                sys.exit()
            elif "Jenkinsfile successfully validated." not in j_validate_response.text:
                print("\n\n"+j_validate_response.text)
                print(" To ignore jenkinsfile validation message use -i flag\n\n")
            else:
                # Validation is successful 
                sleep(0.05)
                self.spinner.text =j_validate_response.text
        except Exception as e:
            print(f"\n\n Exception Error : {e} \n\n") 
            sys.exit()
        self.spinner.text ="Jenkinsfile Validated "
        sleep(0.05)

    def validate_args(self):
        # Check for username 
        if self.arguments["--user"] is None:
            # Does env exist
            if not os.environ.get('JENKINS_USER'):
                print("\n\nPlease provide jenkins username via --user argument or JENKINS_USER env vars\n\n")
                sys.exit()
        # Check for API token
        if self.arguments["--token"] is None:
            # Does env exist
            if not os.environ.get('JENKINS_PASSWORD'):
                print("\n\nPlease provide jenkins API token via --token argument or JENKINS_PASSWORD env vars\n\n")
                sys.exit()
        # Validate user credentials        
        try:
            check= requests.get(self.url,auth=(self.jenkins_user, self.jenkins_password), verify=False)
            if check.status_code == 401 or check.status_code == 403:
                print(f"\n\n Check your credentails/permissions (HTTP {check.status_code} Error ) \n\n")
                sys.exit()    
            elif check.status_code != 200:
                print(f"\n\n Check your Jenkins url {self.url}, it does not seem to be running")
                print(f"(HTTP {check.status_code} Error ) \n\n")
        except Exception as e:
            print(f"\n\n Exception Error : {e} \n\n") 
            sys.exit()
        # Check auth - get crumbs
        self.get_crumb()
        # Validate/Lint jenkinsfile if ignore flag is not set
        if not self.arguments["--ignore-linting"]:
            self.validate_jenkinsfile()

    def main(self):
        # print(self.arguments)
        self.spinner.start()
        sleep(0.05)
        self.spinner.text = "Validate input arguments"
        self.validate_args()
        atexit.register(self.exit_handler)
        self.spinner.text = "Check if job exists"
        # Check if Build Job/Pipeline exists 
        if self.if_job_exits():
            self.spinner.text = "Job found"
            sleep(0.05)    
            self.spinner.text = '  1. Get existing config xml  '    
            sleep(0.05)    
            self.config_file_path = self.get_config_xml()
            self.spinner.text =self.config_file_path
            # - check if params exist
            # - check if generated params file exists locally
            #     - grab params
            #     - generate yaml file out of params
            # - Pass params file to trigger job

            sleep(0.05)    
            self.spinner.text = '2. Update xml'    
            sleep(0.05)    
            self.update_job_config()
            self.spinner.text = '3. Reconfigure/Upload config xml'    
            sleep(0.05)    
            self.upload_job_config()
            self.spinner.text = 'Updating Finished  '    
            sleep(0.05)   
        else:
            # Create new job/pipelinejobjob
            self.spinner.text = '  Creating job:{}  '.format(self.job)    
            sleep(0.05)    
            self.spinner.text = '1. Use template xml'    
            sleep(0.05)    
            self.spinner.text = '2. Update template xml'
            sleep(0.05)    
            self.create_new_config_xml()
            self.spinner.text = '3. Create job with xml'
            sleep(0.05)    
            self.create_new_job()
            self.spinner.text = 'Finished creating job'
            sleep(0.05)
        # Trigger job after checking job exits    
        if self.if_job_exits():
            self.get_crumb()
            queue_url = self.trigger_build()
            self.spinner.text = ''
            self.job_number = self.waiting_for_job_to_start(queue_url)
            self.spinner.stop()
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
        self.config_file_path=self.config_dir+"/"+self.config_file
        # print('##{:70}##'.format(self.config_dir+"/"+self.config_file))
        self.spinner.text = self.config_dir+"/"+self.config_file
        sleep(0.05)
        if self.arguments['--parameters-yaml']:
            self.update_config_with_params()

    def get_params_from_yaml(self):
        with open(self.parametersfile, 'r') as outfile:
            data= yaml.safe_load(outfile)
        return data

    def generate_params_via_template(self):
        file_loader = FileSystemLoader(str(Path(__file__).parent / self.template_folder_path))
        env = Environment(loader=file_loader)
        template = env.get_template(self.params_yaml_template)
        output = template.render(params=self.get_params_from_yaml())
        return output

    def create_new_job(self):
        # print('##{:^70}##'.format('  Creating new Jenkins job  '))
        self.spinner.text = "Creating new Jenkins job"
        sleep(0.05)

        # server = jenkins.Jenkins(self.url, username=self.jenkins_user, password=self.jenkins_password)
        with open(self.config_dir+"/"+self.config_file, 'r') as file:
            xml_file = file.read()
        # create_job = server.create_job(self.job,xml_file)
        create_job = self.server.create_job(self.job,xml_file)
        self.brand_new_job = True
        return

    def get_config_xml(self):
        # server = jenkins.Jenkins(self.url, username=self.jenkins_user, password=self.jenkins_password)
        # job_xml = server.get_job_config(self.job)
        job_xml = self.server.get_job_config(self.job)
        self.spinner.text = self.config_file
        sleep(0.05)
        # Create config folder 
        if not os.path.exists(self.config_dir):                                                                                                                                                                                    
            os.makedirs(self.config_dir)
        # Write config xml into folder path
        with open('{}/{}'.format(self.config_dir,self.config_file), 'w') as file:
            file.write(job_xml)
        config_file = '{}/{}'.format(self.config_dir,self.config_file)
        return config_file

    def update_config_with_params(self):
        # Load config xml into file object
        s = open(self.config_file_path).read()
        # Convert xml file object into ordered dict object
        d = xmltodict.parse(s)

        # Object params that need to be injected into xml
        # generated via a yaml template
        yaml_str_obj=self.generate_params_via_template()
        if yaml_str_obj is not None:
            yaml_obj = yaml.load(self.generate_params_via_template())
            # Converted ordered dict to json string
            ordered_dict=json.dumps(d,indent=2)
            # Converted json string to data object
            xml_obj=json.loads(ordered_dict)
            # Copying params into xml obj generated from yaml
            xml_obj['flow-definition']['properties']=yaml_obj['properties']
            # Converting data object(xml) into xml string
            updated_xml_string=xmltodict.unparse(xml_obj,pretty=True)
            # Generating xml file from xml string 
            tree = ET.ElementTree(ET.fromstring(updated_xml_string))
            tree.write(self.config_file_path)



    def update_job_config(self):
        self.spinner.text = "Updating Config"
        sleep(0.05)
        # server = jenkins.Jenkins(self.url, username=self.jenkins_user, password=self.jenkins_password)
        et = xml.etree.ElementTree.parse(self.config_file_path)
        xml_script = et.getroot().find('definition').find('script')
        with open(self.jenkinsfile, 'r') as pipeline_file:
            xml_script.text = pipeline_file.read()
            
        et.write(self.config_file_path)
        # Inject parameter from yaml parameter file
        if self.arguments['--parameters-yaml']:
            self.update_config_with_params()

        self.spinner.text = "Finished updating config"
        sleep(0.05)

    
    def upload_job_config(self):
        self.spinner.text = "Uploading Jenkins file and config"
        sleep(0.05)
        # server = jenkins.Jenkins(self.url, username=self.jenkins_user, password=self.jenkins_password)
        with open(self.config_file_path, 'r') as file:
            xml_file = file.read()
        # reconfigure_job_xml = server.reconfig_job(self.job,xml_file)
        reconfigure_job_xml = self.server.reconfig_job(self.job,xml_file)
        self.spinner.text = "Finished uploading"
        sleep(0.05)

    def get_crumb(self):
        if self.url:
            crumb_url=self.url+"/crumbIssuer/api/json"
            try:
                r = requests.get(crumb_url,auth=(self.jenkins_user, self.jenkins_password), verify=False)
                response = r.json()
                self.crumb=response["crumb"]
                self.spinner.text = response["crumb"]
                sleep(0.05) 
            except Exception as e:
                print(f"\n\n Jenkins URL seems unavailable. Check if Jenkins is working! \n\n Error : {e} \n\n")             
        else:
            print("Check parameters")
            print("url parameter is missing")

    @staticmethod
    def trigger_build_request(self,build_url,params=None):
        self.spinner.text = "Triggering a build via post @ "+ build_url
        sleep(0.05)    
        headers =  {
                        "Jenkins-Crumb":self.crumb
                    }
        try:
            build_request = requests.post(build_url,params=params,auth=(self.jenkins_user, self.jenkins_password), verify=False,headers=headers)
        except Exception as e:
            if build_request.status_code == 401 or build_request.status_code == 403:
                print("\n\n Check account permissions ( must be admin)/ credentails ")
            print(f"\n\n Error with triggering build \n\n Error : {e} \n\n")             

        return build_request


    def trigger_build(self):
        # Make a build request
        if self.parameters is True :
            build_url = str(self.url + "/job/" + self.job + "/buildWithParameters")
            # Get parameters from yaml file
            # Load parameters from  yaml parameters file provided as -p argument 
            yl = self.get_params_from_yaml()
            d={}
            # Convert yaml list items into a dict of key value pairs
            for i in yl:d[i['name']]=i['value']
            self.parameters=d
            build_request = self.trigger_build_request(self,build_url,params=self.parameters)
        else:
            build_url = self.url + "/job/" + self.job + "/build"
            build_request = self.trigger_build_request(self,build_url)
            self.brand_new_job = False
        if build_request.status_code == 201:
            queue_url =  build_request.headers['location'] +  "api/json"
            self.spinner.text = "Build is queued @ " + queue_url
            sleep(0.05)
        else:
            print("\n\nYour build somehow failed\n\n")
            print(build_request.status_code)
            print(build_request.url)
            print(build_request.text)
            exit(1)
        return queue_url

    def waiting_for_job_to_start(self, queue_url):
        # Poll till we get job number
        # print("\nStarting polling for our job to start")
        self.spinner.text = "\nStarting polling for our job to start"
        sleep(0.05)
        timer = self.timer
        waiting_for_job = True 
        while waiting_for_job:
            queue_request = requests.get(queue_url, auth=(self.jenkins_user, self.jenkins_password), verify=False)
            if queue_request.json().get("why") != None:
                # print(" . Waiting for job to start because :", queue_request.json().get("why"))
                self.spinner.text = " . Waiting for job to start because :"+ queue_request.json().get("why")
                
                timer -= 1
                sleep(self.sleep)
            else:
                waiting_for_job = False
                job_number = queue_request.json().get("executable").get("number")  
                # print(" Job is being build number: ", job_number  )
                self.spinner.text = " Job is being build number: "+ str(job_number)
            if timer == 0:
                print(" time out waiting for job to start")
                exit(1)
        # Return the job numner 
        return job_number

    def console_output(self, job_number):
        stream_spinner = Halo(stream=sys.stderr)
        stream_spinner.start('\n')

        print('\n\n')
        print(bcolors.OKCYAN+'#'*74+bcolors.ENDC)
        print(bcolors.OKCYAN+'##{:^70}##'.format("  Started Build [ {} ] - Build # {}    ".format(self.job,self.job_number) )+bcolors.ENDC)
        print(bcolors.OKCYAN+'#'*74+bcolors.ENDC)
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
            stream_spinner.text="\n"
            console_response = console_requests_session.post(job_url, data={'start': start_at }, verify=False,headers=headers)
            content_length = int(console_response.headers.get("Content-Length",-1))
            content_length = int("10")
            if console_response.status_code != 200:
                stream_spinner.text="\n"
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
                    console_string = str(console_response.content.decode("utf-8"))
                    if self.finish_failure_msg in str(console_response.content):
                        stream_spinner.text="\n"
                        sleep(5)
                        print(self.format_console_output(console_string + "😑😑😑😑"))
                        self.job_status = "failed"
                        stream_open = False
                        # sys.exit()
                    elif self.finish_success_msg in console_string:
                        stream_spinner.text="\n"
                        sleep(5)
                        print(self.format_console_output(console_string + "🥳 🥳  🎉🎉🔥🔥💥💥⚡️⚡️"))
                        self.job_status = "success" 
                        stream_open = False
                        # sys.exit()
                    else:
                        stream_spinner.text="\n"
                        self.format_console_output(console_string)

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
        stream_spinner.text="\n"
        stream_spinner.stop()

    def format_console_output(self,console_string):
        
        for line in console_string.split('\n'):
            if "+" in line[0:5]: 
                print(line.replace('+',bcolors.RED  + "+" + bcolors.ENDC))
            elif "[Pipeline]" in line[0:10]:
                print(line.replace('[Pipeline]',bcolors.OKCYAN  + "[Pipeline]" + bcolors.ENDC))
            else:
                if line:
                    print(line)

    def stop_jobs(self):
        # server = jenkins.Jenkins(self.url, username=self.jenkins_user, password=self.jenkins_password)
        # List running jobs
        if self.job_number is not None :
            print("\n ⚠️  Build Aborted ⚠️  🤖 🤖  \n")
            print('#'*74)
            print('##{:^70}##'.format('  Build Stopped [ {} ] build No:[{}]  '.format(self.job,self.job_number)))
            # builds = server.stop_build(self.job,self.job_number)
            builds = self.server.stop_build(self.job,self.job_number)
            print('#'*74)
            print("\n\n")
        else:
            print("No build to stop")
        return
    
    def exit_handler(self):
        if self.job_status:
            if 'fail' in self.job_status or 'success' in self.job_status :
                print('#'*74)
                print('##{:^70}##'.format(' Job [ {} ] build No:[{}]  '.format(self.job,self.job_number)))
                print('#'*74)
                print("\n\n")
        else: 
            self.stop_jobs()
        
    def delete_job(self):
        try:
            self.server.delete_job(self.job)
            print("\n\n")
            print(bcolors.OKCYAN+'#'*74+bcolors.ENDC)
            print(bcolors.OKCYAN+'##{:^70}##'.format("  Job [ {} ] - deleted  {}  ".format(self.job,self.url) )+bcolors.ENDC)
            print(bcolors.OKCYAN+'#'*74+bcolors.ENDC)
            print("\n\n")
        except Exception as e:
            print(f"\n\n Job delete error: {e} \n\n")






    