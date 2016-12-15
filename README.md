# euler: authorization, object storage & search

Euler was a Swiss mathematician, physicist, astronomer, logician and engineer who made important and influential discoveries in many branches of mathematics like infinitesimal calculus and graph theory while also making pioneering contributions to several branches such as topology and analytic number theory.  [wikipedia](https://en.wikipedia.org/wiki/Leonhard_Euler)

## short description

For research projects that need to authenticate with their enterprise ldap, interact with other institutions in a federated manner to manage active and published projects by providing file and search capabilities, the euler project illustrates how to use off-the-shelf components.  Unlike the other approaches, which use a high percentage of custom code, the euler project accomplishes the same goals leveraging mature open source components.

## stories
[Representative use cases](docs/use_cases.md) to drive discussion of distributed multi-tenant authorization needed for inter-institution pan-cancer research.

![image](https://cloud.githubusercontent.com/assets/47808/21162958/fd6b0058-c144-11e6-8321-8172972634fc.png)

## component description

`Authorization` Euler illustrates how the Keystone OpenStack project that provides Identity, Token, Catalog and Policy services for use specifically by the OHSU Search, BMEG and DIRAC. This project aims to deploy Keystone service  as a proof of concept using Docker and can be upgraded easily. Specifically, we use keystone to integrate the institution's `ldap service` and `all roles and project memberships` are maintained in keystone's datastore. See the [keystone service](services/keystone/README.md) for more information on authentication and authorization.

`Object Storage` Euler illustrates how the Swift OpenStack project provides distributed, eventually consistent object/blob store.  Specifically, we use keystone to authorize access to Swift.  A `plugin` is used to monitor file storage and associate files with metadata in search.  By passively monitoring the storage pipeline, the workflow author requires no additional tools to register files. See the [swift service](services/swift/README.md) for more on file services.

`Search` OICR's dcc portal is used as the search portal and engine.  Euler provides login and authorization services.  The swift plugin enhances the dcc portal by providing a `lightweight "add a file"` functionality which was missing from the dcc portal.  This allows the dcc portal to be used for active projects in addition to publishing finished projects. See the [api service](services/api/README.md) for more on api services.



## quick start

* clone this repository
* create an .env file to hold configuration variables

```
# .env file

# keystone:
ADMIN_TOKEN=... a unique string ...
ADMIN_PROJECT_NAME=admin
ADMIN_USER_NAME=admin
ADMIN_DOMAIN_NAME=Default
ADMIN_DOMAIN_ID=default
ADMIN_PASSWORD=... a unique string ...
ADMIN_EMAIL=... a unique email ...
ADMIN_REGION_ID=ohsu
ADMIN_ROLE_NAME=admin
OHSU_ADMIN_LDAP_CN=... ldap admin CN ...
# escape special characters
OHSU_ADMIN_LDAP_PASSWORD=... ldap admin pass ...


# swift plugin
EULER_API_URL=http://api:8000/v0/files

# api:
PROXY_TARGET=https://dcc.icgc.org
ELASTIC_HOST=elastic
ELASTIC_PORT=9200
API_PORT=8000
API_DEBUG=1
API_HOST=0.0.0.0
API_URL=http://api:8000
MONGO_HOST=mongo
MONGO_PORT=27017
MONGO_DBNAME=test
MONGO_USERNAME=
MONGO_PASSWORD=
AUTHENTICATOR_SECRET=...your long string...


```

Then:

* ```docker-compose -f docker-compose.yml -f docker-compose-development.yml up -d```
* configure [keystone](services/keystone/README.md)
* configure [swift](services/swift/README.md)

Note: Euler uses docker-compose file [version 2.1](https://docs.docker.com/compose/compose-file/#/version-21), which requires [docker engine 1.12](https://docs.docker.com/docker-for-mac/) or greater and [docker-compose 1.9](https://github.com/docker/compose/releases) or greater. These may need separate updates to ensure both requirements are met. See links for upgrading information.

We use [docker compose extends](https://docs.docker.com/compose/extends/) in addition to .env to manage dev vs test. Additional overrides can be developed for different contexts... prod and exacloud vs sparkdmz.


![image](https://cloud.githubusercontent.com/assets/47808/21245920/4ed93a86-c2da-11e6-9f55-27387ab04c0d.png)


## potentially useful aliases

```
alias up="docker-compose -f docker-compose.yml -f docker-compose-development.yml -f docker-compose-openstack.yml up"
alias stop="docker-compose -f docker-compose.yml -f docker-compose-development.yml -f docker-compose-openstack.yml stop"
alias build="docker-compose -f docker-compose.yml -f docker-compose-development.yml -f docker-compose-openstack.yml  build"

execfunction() {
    docker exec -it $1 bash
}
alias exec=execfunction

recreatefunction() {
    stop $1 ; docker rm $1 ; docker rmi euler_$1 ; up -d $1
}
alias recreate=recreatefunction
```
