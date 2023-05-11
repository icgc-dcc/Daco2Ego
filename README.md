# Daco2Ego
Utility and service to load DACO list into Ego.

> **Note**: This script requires 2 ego clients:
> - client.base_url is the DCC Ego instance, and is the service where user management for the DACO groups takes place.
> - daco_v2_client.ego_url is the ARGO Ego instance, which is needed to acquire permissions for Daco2Ego to communicate with the dac-api (DACO V2 system) to retrieve the approved users list.

Installation instructions:

1) Go to the machine you want to run Daco2Ego on, create a daco2ego user, 
grant it permissions to read it's input files from the directory where they're stored, (eg. from /nfs/icgc-dcc), and copy over a configuration file with the right values set. (See the example file for the fields to fill in.)

2) scp over the crontab file, and add it to the daco2ego user's crontab.

```
scp crontab daco2ego@<host>:crontab
ssh daco2ego@<host>
crontab crontab 
```

That's it! 

## Development
Requires Python 3.6 due to the use of format strings. 

To test the script with local ego and dac-api instances (http), enable insecure transport. In daco2ego.py, below the other imports, add:

```
import os
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
```
**Make sure to remove in production!**

## Tests

### Test ego client

File: [test_ego_client.py](./python/tests/test_ego_client.py)

Can be run against a local ego instance, if `OAUTHLIB_INSECURE_TRANSPORT` is enabled (see [Development note](#development)).
Requires a test config file, to be created in `/python/tests/test_ego.conf`. Add in the applicable values:

```
{
  "client": {
    "base_url": "<your_local_ego>",
    "client_id": "<daco2ego_client_id>",
    "client_secret": "<daco2ego_client_secret>",
    "daco_group": "<daco_group_name>",
    "cloud_group":"<daco_cloud_group_name>"
  }
}
```

### Test daco client

File: [test_daco_client.py](./python/tests/test_daco_client.py)

No test config required

### Test daco2ego

File: [test_daco2ego.py](./python/tests/test_daco2ego.py)

Requires a test config file, to be created in `/python/tests/test.conf`, required:
```
  {
    "client":
      {
        "base_url": "https://ego/v1/",
        "dac_api_url": "https://dac-api/v1"
      }
  }
```
