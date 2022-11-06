

## Best pratices

### Services list
There **should** be only one service by folder:
For example, le folder `traefik/` contains all the necessary configuration to
run the `traefik` service.

Thus each folder represent an available service.

The directory must follow the following architecture:
```
service/
├── conf
│   └── ...
├── data
│   └── ...
├── docker-compose.servicename.yml
├── logs
│   ├── access.log
│   └── error.log
└── README.md
```

If the service you are adding can use volumes:
 - `data/`, is where to store to service data
 - `conf/`, is where to store to service configuration
 - `logs/`, is where to store to service logs (others than Docker logs)


#### Environment variables (App)

Generic App variables:
```

# Image management
APP_IMAGE: Defaulted to: APP_IMAGE_NAME:APP_IMAGE_VERSION
APP_IMAGE_VERSION: defaulted to latest
APP_IMAGE_NAME: 

# Main services
APP_NAMESPACE: Name of the namespace
APP_SERVICE: Name of the service, defaulted to the only one
APP_NETWORK: Network name to attach the service

# Expose: Proxy
APP_NAME: App name, defaulted tyo service name
APP_DOMAIN: App top domain
APP_FQDN: App FQDN, defaulted to APP_NAME+APP_DOMAIN

# Expose: Docker
APP_EXPOSE_PORT: Port to expose
APP_EXPOSE_IP: IP to expose

# Docker data directories
APP_CONF_DIR: App configuration dir
APP_DATA_DIR: App internal data dir
APP_SHARE_DIR: App shared data dir, like exports
APP_LOG_DIR: App logs dir

# Other
APP_DEBUG=True/False
APP_TZ=America/Toronto
APP_PGID= App GID
APP_PUID= App UID

```

App settings
```
APP_ADMIN_USER=
APP_ADMIN_PASSWORD=
APP_ADMIN_EMAIL=

APP_TOKEN=
APP_SECRET=
```

#### Environment variables (Services)

LDAP settings
```
LDAP_PROT
LDAP_HOST
LDAP_URL: Defaulted to APP_LDAP_PROT://+APP_LDAP_HOST

LDAP_BIND_DN
LDAP_BIND_USER
LDAP_BIND_PASSWORD
```

MySQL settings:
```
MYSQL_ROOT_PASSWORD
MYSQL_USER
MYSQL_PASSWORD
MYSQL_DATABASE
```

PgSQL settings:
```
PGSQL_ROOT_PASSWORD
PGSQL_USER
PGSQL_PASSWORD
PGSQL_DATABASE
```

Traefik settings:
```
TRAEFIK_SVC_NAME:
TRAEFIK_SVC_DOMAIN:
TRAEFIK_SVC_CERTRESOLVER:
TRAEFIK_SVC_MIDDLEWARES:
TRAEFIK_SVC_ENTRYPOINTS:
...
```

Object Storage settings:
```
S3_ENDPOINT=
S3_USER=
S3_PASSWORD=
S3_BUCKET=
```

Others:
```
JAVA_OPTS
```

