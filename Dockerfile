FROM public.ecr.aws/lambda/python:3.10

COPY requirements.txt ./src/lambda_function.py ./src/sms_aichat.py ${LAMBDA_TASK_ROOT}

RUN pip install -r requirements.txt

CMD ["lambda_function.handler"]
