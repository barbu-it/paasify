# Paasify

Deploy docker-compose files with ease!

Paasify is a little tool that will help deploying `docker-compose.yml` based apps, either on docker swarm 
or on regular docker (via docker-compose). It will also manage the different git repositories 
you need to build your infrastructure. This project try to overstep the missing gap between the 
docker-compose deployment easiness and infrastructure as a code. Also, this project propose an 
opiniated devops workflow and try to provide a smart Infrastructure as Code workflow.

## Quickstart

### Installation

Install paasify:
```
pip install paasify
```

Create your project structure and create empty config file:
```
mkdir my_project
cd my_project
touch paasify.yml
```

Create a simple configuration:
```
sources:
  default:
    url: http://github.com/mrjk/default_coll.git
stacks:
  - default:traefik
  - default:wordpress
  - default:phpmyadmin
```

Then start your stack:
```
paasify apply
```

You can now access to your wordpress instance on [localhost](http://traefik.localhost)

But you may now want to be able to add a network, in wordpress:
```
cat wordpress/docker-compose.yml
networks:
  custom_net:
    name: toto
    external: True
services:
  wordpress:
    networks:
      custom_net
    labels:
      traefik.service.domain: myblog.localhost
```

Then apply your changes:
```
paasify apply
```

This is a very simple case achieved with very few line of code, But
paasify provides plenty of other features:

* Variables management
* Tag management
* Collections and apps
* Collections repositories
* Extensible jsonnet plugin support

Please check the doc and examples to know more.


## Informations

This project is Python3 rewrite of paasify. This project is licensed under GPLv3 license.

### Authors

This project is brought to you thanks to Barbu-IT.

### Releases

* alpha: 


