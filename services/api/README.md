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


  ![image](https://cloud.githubusercontent.com/assets/47808/21246256/6a747d1c-c2dc-11e6-8f80-d9304d8e0925.png)




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
export EVE_SETTINGS=$(pwd)/settings.py

# set test user - should have access to only one project 'BRCA-UK'
export TEST_OS_PASSWORD="password"
export TEST_OS_USERNAME="test_user"
export TEST_OS_USER_DOMAIN_NAME="testing"

# then start tests
py.test --flake8 --cov=. --cov-report term-missing

---------- coverage: platform linux2, python 2.7.11-final-0 ----------
Name                                                Stmts   Miss  Cover   Missing
---------------------------------------------------------------------------------
conftest.py                                            23      0   100%
dcc_proxy.py                                          125      0   100%
eve_util.py                                             4      0   100%
keystone_authenticator.py                              73      0   100%
keystone_connector.py                                  39      0   100%
publisher.py                                            3      0   100%
run.py                                                 61      0   100%
settings.py                                            23      0   100%
tests/integration/api_tests.py                         28      0   100%
tests/integration/keystone_authenticator_tests.py      88      0   100%
tests/integration/keystone_connector_tests.py          25      0   100%
tests/integration/proxy_tests.py                       89      0   100%
tests/integration/schema_tests.py                       1      0   100%
tests/integration/static_tests.py                      20      0   100%
---------------------------------------------------------------------------------
TOTAL                                                 602      0   100%
```
