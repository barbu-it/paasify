# Default paasify collection

This collection provides the most basic services that most of people needs to bootstrap
simple infras. This collection provides an opiniated library and also some helpers. Ultimately
you will want to make your own collections wich fit the way you deploy your infra.

Also, there are some other good collections to complement this one:

* [Barbu-IT Infrastructure](https://github.com/barbu-it/paasify-collection-infra): Devops oriented apps
* [Barbu-IT Community](https://github.com/barbu-it/paasify-collection-community): Apps for everybody


!!! danger "This collection is not stable yet!"

    This collection is not stable YET, the API and the variables will probably change in the future. Be prepared to update your configs on next release.


## Collection file structure

The idea is to stick to what of most of people do, a git repository in
which each folder contains one or more `docker-compose.yml` file, with
eventually some other useful assets, such as extra scripts or config
files, even a build directory sometimes. Also, as this structure is
quite used by most of people, it become possible to integrate complex
applications deployements into paasify (some projects like AWX requires the usage
of a script to template the final `docker-compose.yml` file)


## File structure

The rules are simple (but maybe not 100% fixed for now):

* Every directory containing a `docker-compose.yml` file is considered as an app, unless the names start by an underscore (`_`).
* Every files ending with `.jsonnet` in the `.paasify/plugins` directory is considered like a jsonnet tag.
* One `README.md` for you
* One `mkdocs.yml` to generate a static documentation. Paasify can generate it for you :-)


To give you an (truncated) overview of the file structure of this collection:

```
$ tree -a
.
|-- .git/ <truncated>                   # This is a git repository
|-- .paasify                            # Directory where Paasify can work
|   |-- docs                            # Where documentation can be generated
|   `-- plugins                         # Where jsonnet plugins lives
|       |-- _p.libsonnet                    # Internal helper library
|       |-- _paasify.jsonnet                # Standard library
|       |-- docker-debug.jsonnet
|       |-- docker-net-attach.jsonnet
|       |-- docker-net-provide.jsonnet
|       |-- example.jsonnet
|       |-- homepage.jsonnet
|       |-- mysql-adminer.jsonnet
|       |-- paasify.libsonnet
|       |-- test-paasify-api.jsonnet
|       |-- traefik-mw.jsonnet
|       `-- traefik-svc.jsonnet
|-- README.md                               # This file !
|-- debug                                   # First minimal app, called debug.
|   `-- docker-compose.yml                  # This file is always required
|-- dns                                     # Another app
|   `-- docker-compose.yml
|-- dummy
|   |-- README.md
|   |-- docker-compose.yml
|   `-- vars.yml
|-- example
|   |-- README.md
|   `-- docker-compose.yml
|-- home
|   |-- docker-compose.yml
|   |-- icons
|   |   |-- authentik.png
|   |   |-- ipinfo.png
|   |   `-- whoami.png
|   `-- vars.yml
|-- network
|   `-- docker-compose.yml
`-- proxy                                   # What shoul be an app
    |-- README.md                           # App README.md
    |-- docker-compose.auth.yml             # Many variants
    |-- docker-compose.debug.yml            # ...
    |-- docker-compose.expose_admin.yml     # ...
    |-- docker-compose.expose_dns.yml
    |-- docker-compose.expose_http.yml
    |-- docker-compose.expose_https.yml
    |-- docker-compose.le-dns.yml
    |-- docker-compose.le-tls.yml
    |-- docker-compose.redirect_http.yml
    |-- docker-compose.yml                  # Default docker-compose
    |-- init.sh                             # A little script to help
    `-- vars.yml                            # App vars

```
