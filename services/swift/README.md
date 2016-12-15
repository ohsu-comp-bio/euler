This PR contains:

* an implementation of swift object store, implemented using the existing keystone authentication service

* example user/project setups

* an implementation of the a swift pipeline observer to harvest file additions and notify downstream systems (dcc & bmeg )


A code review would be very helpful.

@kellrott @ksonmez @mayfielg @k1643  @adamstruck @buchanae @prismofeverything: can you review and comment

@AAMargolin @jacmarjorie :FYI


-----




# swift


Simple deployment of a "all in one" style OpenStack Swift server, uses Ubuntu packages as opposed to source.

The Swift implementation is tied to the Keystone sibling project for authentication and authorization.  All data is stored in a docker volume container.

### capabilities

![image](https://cloud.githubusercontent.com/assets/47808/21116547/de3a630c-c06a-11e6-92ba-7922edbed2c6.png)

* As files are added to the object store by an authenticated user, they are published to a message queue where they can be consumed by different systems [dms, bmeg, other...]

* When  an authenticated user queries using the dcc portal or a client tool, they results they see are based on the authorizations assigned to their identity as provided by the institutional ldap server

### data flows

![image](https://cloud.githubusercontent.com/assets/47808/21244620/5984d082-c2d3-11e6-8576-397a419409ec.png)


* (0) - the projects' meta data and files are loaded into dcc (aka '[release](https://github.com/icgc-dcc/dcc-release)')
* (1,2) - An authenticated user adds a file to the object store, and the[ euler plugin](https://github.com/ohsu-computational-biology/euler/blob/swift/services/swift/files/euler.py) picks up meta data about the container, object(file) and user account and posts it to [euler's api service](https://github.com/ohsu-computational-biology/euler/tree/swift/services/api) for processing.
* (3) - The euler api server consumes the event and composes a[ Resource message](https://github.com/ohsu-computational-biology/bioschemas/blob/icgc/bioschemas/snapshot/proto/bmeg/core.proto) and publishes it to a kafka topic.   A kafka component picks up the message and uses existing calls to the dcc-server(which depends on es,mongo) to retrieve context data and creates a [file centric document ](https://github.com/ohsu-computational-biology/bioschemas/blob/icgc/bioschemas/snapshot/jsonschema/icgc-dcc/schema.json). `//todo`
* (4) - An authenticated user, using the either the portal or a command line tool, queries for resources or metadata.   The euler api component filters and redacts those calls.  `//todo`
* (5) - The euler api component relies on keystone for identity and authorization decisions.


## usage

* Startup - nothing special, included in the docker-compose setup.
* Defining users, projects, etc.   This is is covered in the main readme in the euler/keystone repo.


### swift server config setup

* On  keystone server, create a user, service roles and endpoints for swift [see here](http://docs.openstack.org/mitaka/install-guide-ubuntu/swift-controller-install.html)


```
os user create --domain default --password-prompt swift
os role add --project service --user swift admin
os  project create --description "Service Project" service
os role add --project service --user swift admin
os role add --project service --user admin  admin
os service create --name swift   --description "OpenStack Object Storage" object-store
os endpoint create --region oshu object-store public http://swift:8080/v1/AUTH_%\(tenant_id\)s
os endpoint create --region ohsu object-store internal http://swift:8080/v1/AUTH_%\(tenant_id\)s
os endpoint create --region ohsu object-store admin http://swift:8080/v1
```

### verify swift operation

On swift server, defining containers, uploading files,etc.


```
export OS_AUTH_URL="http://controller:35357/v3"
export OS_IDENTITY_API_VERSION="3"
export OS_PASSWORD=ADMIN_PASS
export OS_USERNAME="swift"
export OS_USER_DOMAIN_ID="default"
export OS_PROJECT_DOMAIN_ID="default"
export OS_PROJECT_NAME="service"
alias os=openstack


# # verify it came up
# swift stat
Account: AUTH_1e486beffa674390b406bb868fe8397f
Containers: 0
Objects: 0
  Bytes: 0
X-Put-Timestamp: 1481332328.94644
X-Timestamp: 1481332328.94644
X-Trans-Id: txcc9926ae4d9f457588038-00584b5667
Content-Type: text/plain; charset=utf-8
root@0724c2d89fe6:/# openstack container  list


# # create container and upload file
# os container create container1
# ls -l > /tmp/FILE1
# swift upload  container1  /tmp/FILE1  -H "content-type:text/plain" -H "X-Object-Meta-color:blue"
+------------+------------+----------------------------------+
| object     | container  | etag                             |
+------------+------------+----------------------------------+
| /tmp/FILE1 | container1 | 0c9018bbd7936cdcf0bf0726c1127261 |
+------------+------------+----------------------------------+

# os object  show  container1  tmp/FILE1
+----------------+-----------------------------------------+
| Field          | Value                                   |
+----------------+-----------------------------------------+
| account        | AUTH_1e486beffa674390b406bb868fe8397f   |
| container      | container1                              |
| content-length | 1071                                    |
| content-type   | text/plain                              |
| etag           | 9863d4db04bb6ba178dd84fdc9c54680        |
| last-modified  | Sat, 10 Dec 2016 05:29:06 GMT           |
| object         | tmp/FILE1                               |
| properties     | Color='blue', Mtime='1481347551.599294' |
+----------------+-----------------------------------------+

# # assign capabilities to other groups
# swift post container1 --read-acl "0369f74274b1499eb9257994b8b67087:*" --write-acl "0369f74274b1499eb9257994b8b67087:*"
# swift post container1 --read-acl "d53c2eea749a44a0931ee77fd4c5dcce:*" --write-acl "d53c2eea749a44a0931ee77fd4c5dcce:


# # experiment with other identities ...
# unset OS_USER_DOMAIN_ID
# export OS_USER_DOMAIN_NAME=testing
# export OS_PASSWORD=password

# export OS_PROJECT_NAME=baml
# export OS_USERNAME=baml_user
# # experiment ... os container create baml_container


# export OS_USERNAME=brca_user
# export OS_PROJECT_NAME=brca
# # experiment ... os container create brca_container

# export OS_USERNAME=ccc_user
# export OS_PROJECT_NAME=ccc
```

## extension

This project includes an extension Swift, the OpenStack Object Storage project, so it performs extra action on files at upload time.
We're going to build an `DMS observer` inside Swift. The goal is to observe the new file, harvest the attributes of the resource, the project and account and forward it via kafka to one or more downstream consumers.


To do our observation, we use Swift's pipeline architecture. Swift proxy uses, like many other OpenStack projects, paste to build his HTTP architecture.

Paste uses WSGI and provides an architecture based on a pipeline. The pipeline is composed of a succession of middleware, ending with one application. Each middleware has the chance to look at the request or at the response, can modify it, and then pass it to the following middleware. The latest component of the pipeline is the real application, and in this case, the Swift proxy server.

![image](https://cloud.githubusercontent.com/assets/47808/21115361/d97f0c50-c065-11e6-9c75-514654d5652f.png)

This container implements Swift, where we've added our observer to the default pipeline in the swift-proxy.conf configuration file:


See `euler` we've added to the pipeline in the swift-proxy.conf configuration file:

```
[pipeline:main]
pipeline = catch_errors gatekeeper healthcheck proxy-logging cache container_sync bulk ratelimit euler authtoken keystoneauth copy container-quotas account-quotas slo dlo versioned_writes proxy-logging proxy-server
```

Euler has a simple configuration that basically just tells swift where to load it.  The `Dockerfile` copies the euler.py to the correct installation path.

```
[filter:euler]
paste.filter_factory = swift.common.middleware.euler:filter_factory
set log_level = DEBUG
set log_headers = True
```

You can read more about WSGI [here](http://docs.openstack.org/developer/keystonemiddleware/middlewarearchitecture.html), but this is all that should be necessary to harvest [all](http://docs.openstack.org/developer/swift/proxy.html) the information from the object store.

```

    def __call__(self, env, start_response):
        """
        WSGI entry point.
        Wraps env in swob.Request object and passes it down.

        :param env: WSGI environment dictionary
        :param start_response: WSGI callable
        """

        if not env['REQUEST_METHOD'] in ('PUT', 'COPY', 'POST'):
            return self.app(env, start_response)

        response = None
        try:
            # complete the pipeline
            response = self.app(env, start_response)
            # we want to query the api after the file is stored
            # harvest container, account and object info
            container_info = get_container_info(
                env, self.app, swift_source='Euler')
            self.logger.debug("env: {}".format(env))
            self.logger.debug("container_info: {}".format(container_info))

            account_info = get_account_info(
                env, self.app, swift_source='Euler')
            self.logger.debug("account_info: {}".format(account_info))

            object_info = get_object_info(
                env, self.app)
            self.logger.debug("object_info: {}".format(object_info))
        except:  # catch *all* exceptions
            tb = traceback.format_exc()
            self.logger.debug("traceback: {}".format(tb))

        finally:
            # unaltered upstream response
            return response

```




## reading


https://github.com/openstack/kolla
https://github.com/ccollicutt/docker-swift-onlyone
http://docs.openstack.org/mitaka/install-guide-ubuntu/swift-controller-install.html
https://gist.github.com/briancline/8119051
http://docs.openstack.org/developer/openstack-ansible/developer-docs/quickstart-aio.html
https://ask.openstack.org/en/question/97991/newton-not-a-valid-cloud-archive-name/
