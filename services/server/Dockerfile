FROM java:8-jre

ENV DCC_HOME /opt/dcc
RUN useradd -m dcc &&  mkdir -p $DCC_HOME

ENV RELEASE=4.3.27

WORKDIR $DCC_HOME

ADD https://artifacts.oicr.on.ca/artifactory/dcc-release/org/icgc/dcc/dcc-portal-server/${RELEASE}/dcc-portal-server-${RELEASE}-dist.tar.gz $DCC_HOME

RUN tar xf dcc-portal-server-${RELEASE}-dist.tar.gz && \
    rm dcc-portal-server-${RELEASE}-dist.tar.gz

RUN sed -i.bak s/spring.profiles.active=.*$/spring.profiles.active=ohsu-dev/ ${DCC_HOME}/dcc-portal-server-${RELEASE}/conf/wrapper.conf
RUN cat dcc-portal-server-${RELEASE}/conf/wrapper.conf
COPY conf/portal.yml ${DCC_HOME}/dcc-portal-server-${RELEASE}/conf/application.yml

WORKDIR $DCC_HOME/dcc-portal-server-${RELEASE}


EXPOSE 9000 9200 9300
CMD bin/dcc-portal-server start && tail -F logs/dcc-portal-server.log
#CMD java -jar lib/dcc-portal-server.jar --spring.profiles.active=test --spring.config.location=conf/application.yml
#CMD java -jar lib/dcc-portal-server.jar --spring.profiles.active=ohsu-dev --spring.config.location=conf/
