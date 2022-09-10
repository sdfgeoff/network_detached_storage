
FROM python:3.9

WORKDIR /nds-core

COPY ./requirements.txt /nds-core/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./app /code/app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]