# Daco2Ego
Utility and service to load DACO list into Ego.

Installation instructions:

1) Build the latest docker image and push it to docker_hub
```
./build_remote_docker_image <local_name> <remote_name>
```
(defaults to daco2ego:latest for the local name, and kevinhartmann/daco2ego:latest) for the remote name.

2) Go to the machine you want to run Daco2Ego on, create a daco2ego user, 
grant it permissions to read it's input files (from /nfs/icgc-dcc), copy in
a configuration file with the proper AES and Ego keys set.

3) scp over the crontab file, and add it to the daco2ego user's crontab.
``
scp crontab daco2ego@<host>:crontab
ssh daco2ego@<host>
crontab crontab 
```

