# repository query

```
%7B%22file%22:%7B%22repoName%22:%7B%22is%22:%5B%22Collaboratory+-+Toronto%22%5D%7D%7D%7D&from=1&include=facets&size=25

{
  filters: ,
  from:1,
  include:facets,
  size:25
}

FILTERS='{"file":{"repoName":{"is":["Collaboratory - Toronto"]}}}'
FILTERS=%7B%22file%22:%7B%22repoName%22:%7B%22is%22:%5B%22Collaboratory+-+Toronto%22%5D%7D%7D%7D
API=http://api:8000
curl $API/api/v1/repository/files?filters=$FILTERS'&from=1&include=facets&size=25'


```

import urllib
import os
import requests
proxy_url = 'http://api:8000'
os.environ['FILTERS'] = '{"file":{"repoName":{"is":["Collaboratory - Toronto"]}}}'


filter = urllib.quote_plus(os.environ.get('FILTERS'))
params = { 'filters': filter, 'from': 1 , 'include': 'facets', 'size': 25 }
r = requests.get('{}/api/v1/repository/files'.format(proxy_url), params=params)
print r.json().keys()
