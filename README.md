
# Jenkins Rapid 

A commandline tool to quickly develop/debug Jenkins piepline using jenkinsfiles

## Features

- Upload jenkinsfile from local
- Create/Update jobs (with parameters too)
- Triggers builds
- Streams log output to terminal
- Stop running jobs you’ve started
- Delete jenkins jobs
- Work with Jenkinsfiles directly from your favorite IDE



## Usage: 

#### Create and trigger job

        
            $ jrp --job <job_name> --file <jenkinsfile >--url <jenkins_url> --user <username> --token <user_api_tokern>





## Install 

        $ pip3 install jenkins-rapid

## Config  

- Only generated API tokens will work
- Environment variables can be set for the following values for jenkins url and user credentials and will take presedence over commandline arguments 

        export JENKINS_URL=http://localhost:8080
        export JENKINS_USER=admin
        export JENKINS_PASSWORD=<jenkins_api_token>


        # Deletes job
            $ jrp delete --job <job_name> --url <jenkins_url> --user <username> --token <user_api_tokern>




### Passing build parameters

Build parameters can be passed using a yaml file. See example below

        ---
        - name: PARAM1
          value: some value
        - name: TEST_PARAM2
          value: 19
        - name: TEST_PARAM3
          value: 999
        - name: TEST_PARAM4
          value: morevalues
        - name: SOME_PARAM
          value: obscure value



