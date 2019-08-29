
# Jenkins Rapid 

A commandline tool to quickly debug Jenkins piepline files



## Install 

        $ pip install git+https://git.nbnco.net.au/sec/jenkins-rapid

## Usage: 

        # Creates a new pipeline and tiggers job
            $ jrp --job <job_name> --url <jenkins_url> --user <username> --token <user_api_tokern>
        # Deletes job
            $ jrp delete --job <job_name> --url <jenkins_url> --user <username> --token <user_api_tokern>


## Features

- Creates pipelines if name does not exist
- Overwrites existing pipeline
- Triggers build 
- Displays Jenkins console logs get tailed directly get to user terminal
- Stop running job when user exits console logs 


## Additonal info 

- Environment variables can be set for the following values for jenkins url and user credentials and will take presedence over commandline arguments 

        JENKINS_URL
        JENKINS_USER
        JENKINS_PASSWORD