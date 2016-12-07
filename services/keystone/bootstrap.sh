#!/bin/bash
set -x

# Init the arguments
ADMIN_TOKEN=${ADMIN_TOKEN:-294a4c8a8a475f9b9836}
ADMIN_PROJECT_NAME=${ADMIN_PROJECT_NAME:-admin}
ADMIN_USER_NAME=${ADMIN_USER_NAME:-admin}
ADMIN_PASSWORD=${ADMIN_PASSWORD:-ADMIN_PASS}
ADMIN_EMAIL=${ADMIN_EMAIL:-${ADMIN_USER_NAME}@example.com}
ADMIN_REGION_ID=${ADMIN_REGION_ID:-ohsu}
ADMIN_ROLE_NAME=${ADMIN_ROLE_NAME:-admin}

OS_TOKEN=$ADMIN_TOKEN
OS_URL=${OS_AUTH_URL:-"http://${HOSTNAME}:35357/v3"}
OS_IDENTITY_API_VERSION=3

CONFIG_FILE=/etc/keystone/keystone.conf
OHSU_LDAP_FILE=/etc/keystone/domains/keystone.ohsu.conf

SQL_SCRIPT=${SQL_SCRIPT:-/root/keystone.sql}

if env | grep -qi MYSQL_ROOT_PASSWORD && test -e $SQL_SCRIPT; then
    MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PASSWORD:-$MYSQL_ENV_MYSQL_ROOT_PASSWORD}
    MYSQL_HOST=${MYSQL_HOST:-mysql}
    sed -i "s#^connection.*=.*#connection = mysql://keystone:KEYSTONE_DBPASS@${MYSQL_HOST}/keystone#" $CONFIG_FILE
    mysql -uroot -p$MYSQL_ROOT_PASSWORD -h $MYSQL_HOST <$SQL_SCRIPT
fi

rm -f $SQL_SCRIPT

# update keystone.conf
sed -i "s#^admin_token.*=.*#admin_token = $ADMIN_TOKEN#" $CONFIG_FILE
sed -i "s#OHSU_ADMIN_LDAP_CN#$OHSU_ADMIN_LDAP_CN#" $OHSU_LDAP_FILE
sed -i "s#OHSU_ADMIN_LDAP_PASSWORD#$OHSU_ADMIN_LDAP_PASSWORD#" $OHSU_LDAP_FILE
# DEBUG
cat $CONFIG_FILE

# Populate the Identity service database
keystone-manage db_sync
# Initialize Fernet keys
keystone-manage fernet_setup --keystone-user root --keystone-group root
keystone-manage credential_setup  --keystone-user root --keystone-group root
mv /etc/keystone/default_catalog.templates /etc/keystone/default_catalog

# start keystone service
uwsgi --http 0.0.0.0:35357 --wsgi-file $(which keystone-wsgi-admin) &
# uwsgi --http 0.0.0.0:5000 --wsgi-file $(which keystone-wsgi-public) &
sleep 5 # wait for start

export OS_TOKEN OS_URL OS_IDENTITY_API_VERSION
# Initialize account
keystone-manage bootstrap \
    --bootstrap-password $ADMIN_PASSWORD \
    --bootstrap-username $ADMIN_USER_NAME \
    --bootstrap-project-name $ADMIN_PROJECT_NAME \
    --bootstrap-role-name $ADMIN_ROLE_NAME \
    --bootstrap-service-name keystone \
    --bootstrap-region-id ${ADMIN_REGION_ID} \
    --bootstrap-admin-url http://${HOSTNAME}:35357 \
    --bootstrap-public-url http://${HOSTNAME}:5000 \
    --bootstrap-internal-url http://${HOSTNAME}:5000

unset OS_TOKEN OS_URL

# log any issues
keystone-manage doctor

# Write openrc to disk

cat >~/openrc <<EOF
export OS_USERNAME=${ADMIN_USER_NAME}
export OS_PASSWORD=${ADMIN_PASSWORD}
export OS_PROJECT_NAME=${ADMIN_PROJECT_NAME}
export OS_AUTH_URL=http://${HOSTNAME}:35357/v3
export OS_PROJECT_DOMAIN_ID=${ADMIN_DOMAIN_NAME}
export OS_USER_DOMAIN_ID=${ADMIN_DOMAIN_NAME}
export OS_IDENTITY_API_VERSION=3
EOF

# DEBUG
# cat ~/openrc


# reboot services
pkill uwsgi
sleep 5
uwsgi --http 0.0.0.0:5000 --wsgi-file $(which keystone-wsgi-public) &
sleep 5
uwsgi --http 0.0.0.0:35357 --wsgi-file $(which keystone-wsgi-admin)
