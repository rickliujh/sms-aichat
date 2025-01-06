# A Quasi-production Ready AI Chat Demo

Build with Python, AWS Lambda, Twilio, and Terraform.

This application allow you to chat with LLM through phone number. It could be, later, extended for whats app, discord, etc.

## Table of Content

- How-tos
- Design
- Development
- Infrastructure

## How-tos

### Dependency

This project is using `uv` as package and project manager. If there is no `uv` install in you environment, use this command to install it first.

```
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Make

`make` and Makefile are build system this project use to do most of staff

```
# Install all dependencies for the project

make init

# Build image using local docker

make

# Linting the project

make lint

# Try fix any code issue from linting report

make fix

# Run the tests

make test

# Run lambda handler locally inside of container

make Run

```

### requirements.txt

You can export a requirements.txt file using uv.lock for traditional tool chains

```
make expt
```

### Infrastructure

Spin up infrastructure using terraform. The tf scripts contain both infra in AWS and Github, prep is needed for a few tokens and variable to be setup manually before running `tf apply` if the environment is new.

## Design

### Flow

In order to achieve a functional ai-chat using SMS or whatsapp, we need 3 parts of the puzzle: A LLM inference, A Mobile carrier for SMS, A piece of code that glue that 2 parts together.

This project uses webhook that carrier provided as Lambda trigger. When a SMS is sent to designate number, a HTTP call has made to our lambda handler, along with the message in the SMS, in turn a inference has made to LLM with message as prompt, the code response the HTTP request (webhook) from carrier with result from LLM and ends the procedure.

![Overview](system-overview.png)

### Scale

We assume that mobile carrier as 3th party provider has enough capacity handling the initial request.

The system is design to use API as service for LLM, which means the LLM can be self-hosted or another 3th party provider, ether case the scaling issue can be addressed independently, more details according to this matter is out of scope.

The Lambda handler is server less service, which means it self handles all the scaling issue.

## Development

- A python project design to run specifically on AWS Lambda
    - Using ruff for linting and formating
    - Using Mypy for static code analysis
    - Using Pytest for unit testing
    - Using AWS official lambda image for python to simulate lambda environment in cloud
- Unit test
    - Unit test is placed in ./tests/unit/src
    - Data for unit test is in ./tests/events
    - CI will check on branch `main` or pull request to make sure unit test is satisfied
    - All unit test files will be checked during linting
- Pipeline
    - Pipeline will run on any commit on `main` branch or pull requests
    - 3 stages include
        - test: test the code and linting
        - build: the code will be packaged as Docker Image that push to AWS ECR
        - deploy: A terraform script will run through plan and apply, if pipeline triggered by pull request, a plan will be placed in comment for review, apply will be run after pull request checking in to `main` branch

## Infrastructure

This project uses `terraform` to manage the infrastructure. Includes two part: Github and AWS

![infra design](infra-dialog.png)

### Github

Github variables and secretes that are necessary for running CI/CD pipeline (Github Actions) are managed by Terraform scripts.

Authentication and authorization integration to AWS is through assume role, with each role's permission fine-grained based on different stage of the pipeline, make sure only necessary permissions is granted to Github Actions.

There are three roles to assume during the pipeline workflow.

1. ECR push only role for the build stage in order to have just enough permissions to push image to private ECR repository
2. Terraform plan role with only read only permission to comment on pull request for review
3. Terraform apply role with necessary permissions to update lambda function and any other infrastructures if needed

### AWS

Terraform managed all the infrastructures on AWS, includes: ECR, S3, DynamoDB, Lambda, Cloudwatch, VPC, IAM policies and roles.

- Private ECR stores python code packaged in iamge with version, ready for use
- S3, DynamoDB for Terraform backend state tracking
- Lambda for running python code
- Cloudwatch for logging propose
- VPC in which lambda function is running has security group that only allows incoming traffic from Mobile carrier's ip address
- IAM policies an role are all fine-grained to the minimum permission possible

## References

- 
