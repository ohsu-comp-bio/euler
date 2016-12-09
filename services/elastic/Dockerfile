FROM elasticsearch:5.0.0

RUN apt-get update  && \
    apt-get install -y jq vim

ARG http_proxy
ARG https_proxy
EXPOSE 9200
EXPOSE 9300
