FROM python:2.7

RUN mkdir -p /usr/src/setup
WORKDIR /usr/src/setup

ADD dev-requirements.txt   /usr/src/setup/

RUN apt-get update

RUN apt-get install -y autoconf automake libtool curl make g++ unzip vim libldap2-dev libsasl2-dev python-ldap


RUN pip install pip --upgrade

RUN mkdir $HOME/.python-eggs \
  && chmod og-w $HOME/.python-eggs \
  && pip install -r dev-requirements.txt \
  && pip install ipython \
  && pip install pdb \
  && pip install nose


# mounted volume for source
RUN mkdir -p /service
WORKDIR /service
ENV FLASK_APP=run.py
CMD python run.py
