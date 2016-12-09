# API

##  Features:
* JWT Token BearerAuth that leverages Keystone
  * `/v0/login, /v0/logout`
  * Note: JWT was selected to align with CCC. Keystone supports OAuth1 as well, this has not been tested.
* files endpoint for repo file submission
  * all posts call stub publish() method, eventually this should call kafka  
  * `/v0/files`
* Passthrough proxy to act as an authorization check for all DCC server api calls
  * `/*` any other request is passed to DCC


  ![image](https://cloud.githubusercontent.com/assets/47808/21032712/179a7866-bd60-11e6-935d-a943a65e50d2.png)




## Testing
Is very preliminary at this time.

The tests that do exist are integration tests,
that is they test the API with the backends, no mocks exists.
Therefore, real databases need to exist and the server
needs to be able to connect to them.


```
# run tests from container
$ docker exec -it api  bash

# for some reason, this needs to be set in order to
# for eve to run ( gets config not found otherwise )
$ export EVE_SETTINGS=$(pwd)/settings.py

# then start tests
$ py.test --flake8 --cov=. --cov-report term-missing


---------- coverage: platform linux2, python 2.7.11-final-0 ----------
Name                                                Stmts   Miss  Cover   Missing
---------------------------------------------------------------------------------
conftest.py                                             8      0   100%
eve_util.py                                             4      0   100%
keystone_authenticator.py                              60      0   100%
keystone_connector.py                                  29      0   100%
publisher.py                                            3      0   100%
run.py                                                 35      0   100%
settings.py                                            24      0   100%
tests/integration/api_tests.py                          5      0   100%
tests/integration/keystone_authenticator_tests.py      80      0   100%
tests/integration/keystone_connector_tests.py          25      0   100%
tests/integration/proxy_tests.py                        5      0   100%
tests/integration/schema_tests.py                       5      0   100%
---------------------------------------------------------------------------------
TOTAL                                                 283      0   100%

```

## TODO

* The dcc portal will need screens to /login & /logout

* The proxy will need to implement filters & redaction previously prototyped in javascript.
