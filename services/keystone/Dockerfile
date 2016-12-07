FROM python:2.7
MAINTAINER walsbr "walsbr@ohsu.edu"

# see https://wiki.opnfv.org/display/functest/OpenStack+python+clients
ENV VERSION=10.0.0
ENV CLIENT_VERSION=3.2.0

# update catalog, install keystone dependencies, ldap dependencies,
# dev dependencies & the clean up
RUN set -x \
    && apt-get -y update \
    && apt-get install -y libffi-dev python-dev libssl-dev mysql-client python-mysqldb \
    && apt-get install -y libldap2-dev libsasl2-dev python-ldap \
    && apt-get install -y vim jq sqlite3

# install from git
RUN curl -fSL https://github.com/openstack/keystone/archive/${VERSION}.tar.gz -o keystone-${VERSION}.tar.gz \
    && tar xvf keystone-${VERSION}.tar.gz \
    && cd keystone-${VERSION} \
    && pip install -r requirements.txt \
    && PBR_VERSION=${VERSION}  pip install . \
    && pip install uwsgi MySQL-python \
    && pip install python-ldap \
    && pip install ldappool \
    && pip install pytest \
    && cp -r etc /etc/keystone \
    && cd - \
    && rm -rf keystone-${VERSION}*
RUN pip install  python-openstackclient==${CLIENT_VERSION}

# install from pypi
# RUN set -x && apt-get -y update && apt install -y keystone && apt-get -y clean
# RUN pip install uwsgi MySQL-python \
#  && pip install python-ldap \
#  && pip install ldappool \
#  && pip install pytest \
#  && pip install python-openstackclient


COPY keystone.conf /etc/keystone/keystone.conf
COPY keystone.forumsys.conf /etc/keystone/domains/keystone.forumsys.conf
COPY keystone.ohsu.conf /etc/keystone/domains/keystone.ohsu.conf
COPY keystone.sql /root/keystone.sql

# Add bootstrap script and make it executable
COPY bootstrap.sh /etc/bootstrap.sh
RUN chown root:root /etc/bootstrap.sh && chmod a+x /etc/bootstrap.sh


ENTRYPOINT ["/etc/bootstrap.sh"]
EXPOSE 5000 35357

# need docker 1.12+
HEALTHCHECK --interval=60s --timeout=5s \
  CMD curl -f http://localhost:5000/v3 2> /dev/null || exit 1; \
  curl -f http://localhost:35357/v3 2> /dev/null || exit 1; \
