FROM java:8-jdk

RUN mkdir /dcc

ENV RELEASE=4.3.27
ENV DCC_HOME=/dcc

WORKDIR $DCC_HOME

ADD https://artifacts.oicr.on.ca/artifactory/dcc-release/org/icgc/dcc/dcc-portal-server/${RELEASE}/dcc-portal-server-${RELEASE}-dist.tar.gz ${DCC_HOME}/dcc-portal.tar.gz
RUN \
  tar xf dcc-portal.tar.gz && \
  rm dcc-portal.tar.gz && \
  mv dcc-portal-server-* dcc-portal-server && \
  sed -i.bak s/spring.profiles.active=.*$/spring.profiles.active=ohsu-dev/ ${DCC_HOME}/dcc-portal-server/conf/wrapper.conf && \
  rm ${DCC_HOME}/dcc-portal-server/conf/wrapper.conf.bak && \
  sed -i.bak '2iunset MAIL' ${DCC_HOME}/dcc-portal-server/bin/dcc-portal-server && \
  rm ${DCC_HOME}/dcc-portal-server/bin/dcc-portal-server.bak
COPY conf/portal.yml ${DCC_HOME}/dcc-portal-server/conf/application.yml

RUN ls

WORKDIR $DCC_HOME/dcc-portal-server

RUN ls

CMD java -jar lib/dcc-portal-server.jar --spring.profiles.active=ohsu-dev --spring.config.location=conf/application.yml
