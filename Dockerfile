FROM public.ecr.aws/lambda/python:3.9

COPY requirements.txt ${LAMBDA_TASK_ROOT}
COPY app ${LAMBDA_TASK_ROOT}/app
COPY main.py ${LAMBDA_TASK_ROOT}

RUN pip install -r requirements.txt

CMD ["main.handler"] 