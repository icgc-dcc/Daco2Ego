# Daco2Ego
Utility and service to load DACO list into Ego.

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

To test with a local ego and dac-api (http), enable insecure transport. In daco2ego.py, below the other imports, add:

```
import os
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
```
Make sure to remove in production!