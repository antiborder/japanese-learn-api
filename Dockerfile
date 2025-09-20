FROM public.ecr.aws/lambda/python:3.10

COPY requirements.txt ${LAMBDA_TASK_ROOT}
COPY app ${LAMBDA_TASK_ROOT}/app
COPY google-tts-key.json ${LAMBDA_TASK_ROOT}

RUN pip install -r requirements.txt

CMD ["app.main.handler"] 