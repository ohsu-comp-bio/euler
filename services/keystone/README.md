# keystone: Authentication (authN) and high-level Authorization (authZ).


## Short Description

Euler illustrates how the Keystone OpenStack project that provides Identity, Token, Catalog and Policy services for use specifically by the OHSU Search, BMEG and DIRAC. This project aims to deploy Keystone service  as a proof of concept using Docker and can be upgraded easily.

[Representative use cases](docs/use_cases.md) to drive discussion of distributed multi-tenant authorization needed for multi-institution pan-cancer research.

![image](https://cloud.githubusercontent.com/assets/47808/20950267/9674d14c-bbd3-11e6-9791-55966149880e.png)

[This documentation](http://docs.openstack.org/developer/keystone/) is primarily targeted towards contributors of the project, and assumes that you are already familiar with Keystone from an end-user perspective; however, end users, deployers, and operators will also find it useful.


## Quick Start Using Docker Compose

Simply run:

```docker-compose up -d```

## How to use this image

It may takes seconds to do some initial work, you can use `docker logs` to detect the progress. Once the Openstack Keystone Service is started, you can verify operation of the Identity service as follows:

```
$ docker-compose build keystone
$ docker-compose up -d
$ docker exec -it keystone bash

# in docker container

# setup alias and env
alias os=openstack
source ~/openrc
os  domain  list
# create domains
os  domain  create forumsys
os  domain  create ohsu
os  domain  create testing
# Restart the OpenStack Identity service.....
```

Now `$ exit` out of the keystone container, `docker stop` the container, and restart it with the original `docker-compose up -d`. 
Don't worry, the compose provisions a volume where keystone will store the domains just created. You won't lose work by just stopping and starting the container. 

```
# re-login when it comes up
os  domain  list
# log should display forumsys & ohsu

# now build a representative project structure
os  project  create ccc
os  project  create baml --parent ccc
os  project  create brca --parent ccc
os  project  create BRCA-UK --parent ccc
os  project  create  CLLE-ES  --parent ccc
os  project  create  ALL-US  --parent ccc
os  project  create  LAML-US  --parent ccc
os  project  create  AML-US  --parent ccc
os  project  create  LAML-KR  --parent ccc
os  project  create  CMDI-UK  --parent ccc
os  project  create  MALY-DE  --parent ccc
os  project  create  LAML-CN  --parent ccc
os  project  create  DLBC-US  --parent ccc
os  role create member

# add user

os role add --project ccc --user <any ohsu user> --user-domain ohsu  member
os role add --project baml --user <any ohsu user> --user-domain ohsu  member
```

Failure to stop and restart the container may result in errors connecting to the ldap domains you just created, e.g.
```
No user with a name or ID of '<your-user-name>' exists.
```

```
# create test users
os  domain  create testing
os user create --password password  --domain testing brca_user
os user create --password password  --domain testing baml_user
os user create --password password  --domain testing ccc_user
os user create --password password  --domain testing test_user

os role add --project brca --user brca_user --user-domain testing  member
os role add --project baml --user baml_user --user-domain testing  member
os role add --project brca --user ccc_user --user-domain testing  member
os role add --project baml --user ccc_user --user-domain testing  member
os role add --project ccc --user ccc_user --user-domain testing  member
os role add --project BRCA-UK --user admin --user-domain default  member
os role add --project BRCA-UK --user test_user --user-domain testing  member
os role add --project BRCA-UK --user walsbr --user-domain testing  member


CLLE-ES
ALL-US
LAML-US
AML-US
LAML-KR
CMDI-UK
MALY-DE
LAML-CN
DLBC-US

# show membership
os role assignment list  --name

os role assignment list  --name
+--------+-------------------+-------+-----------------+--------+-----------+
| Role   | User              | Group | Project         | Domain | Inherited |
+--------+-------------------+-------+-----------------+--------+-----------+
| admin  | admin@Default     |       | admin@Default   |        | False     |
| member | <any ohsu>@ohsu   |       | ccc@Default     |        | False     |
| member | <any ohsu>@ohsu   |       | baml@Default    |        | False     |
| admin  | swift@Default     |       | service@Default |        | False     |
| admin  | admin@Default     |       | service@Default |        | False     |
| member | brca_user@testing |       | brca@Default    |        | False     |
| member | baml_user@testing |       | baml@Default    |        | False     |
| member | ccc_user@testing  |       | brca@Default    |        | False     |
| member | ccc_user@testing  |       | baml@Default    |        | False     |
| member | ccc_user@testing  |       | ccc@Default     |        | False     |
+--------+-------------------+-------+-----------------+--------+-----------+

# authenticate (if using OHSU behind firewall)
export OHSU="--os-username <any ohsu user>
--os-auth-url http://controller:35357/v3
--os-user-domain-id <ohsu domain id from domain list>
--os-identity-api-version 3
--os-password <any ohsu password user>"

# these should work
os token issue  $OHSU --os-project-name ccc
os token issue  $OHSU --os-project-name baml

+------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Field      | Value                                                                                                                                                                                                      |
+------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| expires    | 2016-12-07 02:22:39+00:00                                                                                                                                                                                  |
| id         | gAAAAABYR2RfgW1wsOffKsaeok43wbP7HIKewpJaqcmxWsMDryxLlryA2Glo7OQ_ha6vM2KhSzjeQkTi6Ou3z6Erpey_KiSmHpnmr7Z1oi1aByXdJp4f7FURHvDR5oZKg-                                                                         |
|            | 5JQXU_EQesT8R_xsR3wOVtJgjQcVmSp_yXdz5IgzQjj8h8H2uGLd1AJiFX2lxIEI2mUpUnRSSY6jy8TEL_ixDuNRejgHM2Zui0Bmh78dyJVjM6CK7tkKY                                                                                      |
| project_id | 2363da9faceb46b3b54e332966e39f67                                                                                                                                                                           |
| user_id    | ba9096ee5e956e35452227fe6a4f36f994ec34495030763706cdf530f870949e                                                                                                                                           |
+------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

# this should fail
os token issue  $OHSU --os-project-name admin

# authenticate (if using public ldap server forumsys outside firewall)
export FORUMSYS="--os-username tesla
--os-auth-url http://controller:35357/v3  
--os-user-domain-id <forumsys domain id from domain list>
--os-identity-api-version 3     
--os-password password"


os role add --project ccc --user tesla --user-domain forumsys  member
os role add --project baml --user tesla  --user-domain forumsys  member

os token issue  $FORUMSYS --os-project-name baml
+------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Field      | Value                                                                                                                                                                                        |
+------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| expires    | 2016-12-07 05:00:24+00:00                                                                                                                                                                    |
| id         | gAAAAABYR4lYzHAf8oGY2MimaeJXy2I0tcvsfgNrrmJW6k4AJs2ZcPO92so7lVHXitOs_Zn36my0cOFkBAmcAF-4d8JdJY61xfuDcthETYVVN9I_SUzmtOPtMjnoIjkR1tgYZRorY7b9q7I6DSALpZ51MQwox7EHZ_TcCBdlBJZZKv9JC-           |
|            | FUVbfTLzpN_O6jukhPdcWhI_TBw-tGoV5nd308kyXoMr3qwrSMBR20kX81zB6BbamjM6E                                                                                                                        |
| project_id | 0369f74274b1499eb9257994b8b67087                                                                                                                                                             |
| user_id    | 0b42e922b1712df2d994b91eab805aacfdaf4aedc4b8e609284c7f2dc021129b                                                                                                                             |
+------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+


```

## Environment Variables

Before you create a Keystone Service, you can adjust the additional configuration of the Openstack Keystone Service by passing one or more environment variables in .env or on the docker run command line.

```
# .env file
# configuration, read by docker compose, passed to services/keystone/bootstrap.sh
ADMIN_TOKEN=....
ADMIN_PROJECT_NAME=....
ADMIN_USER_NAME=....
ADMIN_DOMAIN_NAME=....
ADMIN_PASSWORD=....
ADMIN_EMAIL=....
ADMIN_REGION_ID=....
ADMIN_ROLE_NAME=....
OHSU_ADMIN_LDAP_CN=....
# escape special characters
OHSU_ADMIN_LDAP_PASSWORD=....
```

## Testing

Test bootstrap setup
`py.test tests/integration/test_bootstrap.py `

## TODO



### mysql

Openstack Keystone Service uses an SQL database (default sqlite) to store data. The official documentation recommends use MariaDB or MySQL.

The compose file needs to be adjusted to use mysql
The following environment variables should be change according to your practice.

* `-e MYSQL_ROOT_PASSWORD=...`: Defaults to the value of the `MYSQL\_ROOT\_PASSWORD` environment variable from the linked mysql container.
* `-e MYSQL_HOST=...`: If you use an external database, specify the address of the database. Defautls to "mysql".

### Federation

In order to integrate to remote providers (google or other keystone instances) the keystone app will need to run under apache.

![image](https://cloud.githubusercontent.com/assets/47808/20950402/4ff71666-bbd4-11e6-8719-b8614050c71d.png)



## Utility

```
alias recreate='docker-compose stop keystone ;  docker-compose rm keystone ; docker rmi euler_keystone ; docker-compose build keystone ;'
```
