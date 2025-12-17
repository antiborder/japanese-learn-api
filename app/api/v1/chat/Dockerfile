FROM public.ecr.aws/lambda/python:3.11

# Copy requirements and install dependencies
# Install numpy and faiss-cpu first (with pre-built wheels if possible)
COPY requirements.txt ${LAMBDA_TASK_ROOT}
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir numpy==1.26.4 && \
    pip install --no-cache-dir faiss-cpu==1.7.4 && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py ${LAMBDA_TASK_ROOT}/
COPY endpoints/ ${LAMBDA_TASK_ROOT}/endpoints/
COPY integrations/ ${LAMBDA_TASK_ROOT}/integrations/
COPY services/ ${LAMBDA_TASK_ROOT}/services/
COPY schemas/ ${LAMBDA_TASK_ROOT}/schemas/
COPY tools/ ${LAMBDA_TASK_ROOT}/tools/

# Set the CMD to your handler
CMD [ "app.lambda_handler" ]

