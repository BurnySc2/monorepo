FROM python:3.6

ADD . /root/template

WORKDIR /root/template

RUN python -m pip install --upgrade pipenv
RUN pipenv install --dev

ENTRYPOINT [ "/bin/bash" ]

