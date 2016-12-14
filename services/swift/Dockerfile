FROM ubuntu:16.04

MAINTAINER walsbr "walsbr@ohsu.edu"

# https://releases.openstack.org/newton/
# https://wiki.opnfv.org/display/functest/OpenStack+python+clients
ENV CLIENT_VERSION=3.2.0
ENV SWIFT_VERSION=2.10.0


# update catalog, install keystone dependencies, ldap dependencies,
# dev dependencies & the clean up
RUN set -x \
    && apt-get -y update \
    && apt-get install -y rsyslog software-properties-common  xfsprogs pwgen \
    libffi-dev python-pip python-dev build-essential libssl-dev \
    vim jq curl unzip \
    memcached rsync supervisor python-netifaces python-xattr python-memcache


# swift controller dependencies
RUN apt-get update -y && apt-get upgrade -y
RUN apt-get install -y software-properties-common
RUN add-apt-repository cloud-archive:newton
RUN apt-get update -y
RUN apt-get install -y  swift python-swiftclient  \
                       swift-proxy swift-object  python-keystoneclient \
                       python-swiftclient swift-plugin-s3  \
                       python-keystonemiddleware \
                       swift-account swift-container


RUN pip install  python-openstackclient==${CLIENT_VERSION}

# Prep files before building docker ...
# curl  https://git.openstack.org/cgit/openstack/swift/plain/etc/proxy-server.conf-sample?h=stable/newton
# TODO memcached local

RUN mkdir -p /var/log/supervisor
ADD files/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

#
# Swift configuration
# - Partially fom http://docs.openstack.org/developer/swift/development_saio.html
#

# not sure how valuable dispersion will be...
ADD files/dispersion.conf /etc/swift/dispersion.conf
ADD files/rsyncd.conf /etc/rsyncd.conf
ADD files/swift.conf /etc/swift/swift.conf
ADD files/proxy-server.conf /etc/swift/proxy-server.conf
ADD files/account-server.conf /etc/swift/account-server.conf
ADD files/object-server.conf /etc/swift/object-server.conf
ADD files/container-server.conf /etc/swift/container-server.conf
ADD files/startmain.sh /usr/local/bin/startmain.sh
ADD files/rsyslog.conf /etc/rsyslog.conf
ADD files/euler.py /usr/lib/python2.7/dist-packages/swift/common/middleware/euler.py

RUN echo 'RSYSLOGD_OPTIONS=""' > /etc/default/rsyslog
RUN chmod 755 /usr/local/bin/startmain.sh

EXPOSE 8080

CMD /usr/local/bin/startmain.sh
