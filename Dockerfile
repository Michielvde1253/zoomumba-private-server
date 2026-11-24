FROM python:3.11-bookworm

ADD . /project
WORKDIR /project
RUN pip install -r requirements.txt

CMD [ "python", "/project/app.py" ]
