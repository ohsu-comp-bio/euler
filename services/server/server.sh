#!/bin/bash

DCC_HOME=/opt/dcc
mkdir -p $DCC_HOME
cd $DCC_HOME

ENV RELEASE=4.3.27

wget https://artifacts.oicr.on.ca/artifactory/dcc-release/org/icgc/dcc/dcc-portal-server/${RELEASE}/dcc-portal-server-${RELEASE}-dist.tar.gz $DCC_HOME
tar xf dcc-portal-server-${RELEASE}-dist.tar.gz && \
    rm dcc-portal-server-${RELEASE}-dist.tar.gz

sed -i.bak s/spring.profiles.active=.*$/spring.profiles.active=ohsu-dev/ ${DCC_HOME}/dcc-portal-server-${RELEASE}/conf/wrapper.conf
cp conf/portal.yml ${DCC_HOME}/dcc-portal-server-${RELEASE}/conf/application.yml

cd $DCC_HOME/dcc-portal-server-${RELEASE}

bin/dcc-portal-server start
