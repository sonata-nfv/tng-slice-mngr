FROM python:3.4-slim
LABEL organization=5GTANGO

# configrurations
#ENV key value

ADD . /tng-slice-mngr

WORKDIR /tng-slice-mngr
RUN python setup.py install

CMD ["python", "main.py"]