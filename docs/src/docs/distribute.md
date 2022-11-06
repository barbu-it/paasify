# Distribute

## Project data

!!! info
    Plugin reference is [available here](/extend/extend_plugins/#project)


Your project should be tracked in a control system, such as git. 

Files project to be commited:
```
paasify.yml
.passify/
  plugins/
    plugin1.jsonnet
.gitignore
stack1/
  data/
  conf/
stack2/
  
```



### Ignored files

Files are considerated as unimportant:

* `.paasify/collections/`: Temporary dir where are stored files

Your project should have a specific .gitignore, created when a project is inited:
```
.paasify/collections/*
*/data/*
*/share/*
*/tmp/*
*/db_data/*

```

## Reusable content

### Apps

!!! info
    Plugin reference is [available here](/extend/extend_plugins/#app)



* explain: vars.yml
* explain: docker-compose.yml



#### Tags (docker-compose)

!!! info
    Plugin reference is [available here](/extend/extend_plugins/#docker-compose-tag)



This example taken from example dir presents how to modularize config.

Example:
``` console
$ ls -1  docker-compose.*
docker-compose.debug.yml
docker-compose.ep_https.yml
docker-compose.yml

$ head -n 999 docker-compose.*
==> docker-compose.debug.yml <==
services:
  traefik:
    environment:
      - TRAEFIK_LOG_LEVEL=debug
      - TRAEFIK_ACCESSLOG=true
      - TRAEFIK_API_DEBUG=true
      - TRAEFIK_ACCESSLOG_FILEPATH=

==> docker-compose.ep_https.yml <==
services:
  traefik:
    ports:
      - "$app_expose_ip:443:443"
    environment:
      # Entrypoints
      - TRAEFIK_ENTRYPOINTS_front-https_ADDRESS=:443 # <== Defining an entrypoint for port :80 named front
      # Forced Http redirect to https
      - TRAEFIK_ENTRYPOINTS_front-http_HTTP_REDIRECTIONS_ENTRYPOINT_PERMANENT=true
      - TRAEFIK_ENTRYPOINTS_front-http_HTTP_REDIRECTIONS_ENTRYPOINT_SCHEME=https
      - TRAEFIK_ENTRYPOINTS_front-http_HTTP_REDIRECTIONS_ENTRYPOINT_TO=front-https

```


### Collections

!!! info
    Plugin reference is [available here](/extend/extend_plugins/#collection)


#### Create a repo


!!! info
    Plugin reference is [available here](/extend/extend_plugins/#repository)


This is a simple git repository where files are commited.


#### Append apps and plugins

TODO:


