FROM public.ecr.aws/lambda/python:3.10

COPY requirements.txt lambda_function.py ${LAMBDA_TASK_ROOT}

RUN pip install -r requirements.tx

CM ["lambda_function.handler"]
