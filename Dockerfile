FROM python:3.4-slim
LABEL organization=5GTANGO

# configurations
ENV SLICE_MGR_PORT 5998
ENV USE_SONATA True

ENV SONATA_GTK_COMMON tng-gtk-common
ENV SONATA_GTK_COMMON_PORT 5000
ENV SONATA_GTK_SP tng-gtk-sp
ENV SONATA_GTK_SP_PORT 5000
ENV SONATA_REP tng-rep
ENV SONATA_REP_PORT 4012
ENV SONATA_CAT tng-cat
ENV SONATA_CAT_PORT 4011

ADD . /tng-slice-mngr

WORKDIR /tng-slice-mngr
RUN python setup.py install

CMD ["python", "main.py"]