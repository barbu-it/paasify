<p align='center'>
<img src="logo/paasify_brand.svg" alt="Paasify">
</p>

<p align='center'>
<a href="https://gitter.im/barbu-it/paasify">
<img src="https://img.shields.io/gitter/room/barbu-it/paasify" alt="Gitter"></a>
<a href="https://pypi.org/project/paasify/">
<img src="https://img.shields.io/pypi/v/paasify" alt="PyPI"></a>
<a href="https://pypistats.org/packages/paasify">
<img src="https://img.shields.io/pypi/dm/paasify" alt="PyPI - Downloads"></a>
<a href="https://github.com/barbu-it/paasify/releases">
<img src="https://img.shields.io/piwheels/v/paasify?include_prereleases" alt="piwheels (including prereleases)"></a>
<a href="https://github.com/barbu-it/paasify/graphs/code-frequency">
<img src="https://img.shields.io/github/commit-activity/m/barbu-it/paasify" alt="GitHub commit activity"></a>
<a href="https://www.gnu.org/licenses/gpl-3.0">
<img src="https://img.shields.io/badge/License-GPL%20v3-blue.svg" alt="License: GPL v3"></a>
</p>

<p align="center">
<img src="https://img.shields.io/pypi/pyversions/paasify" alt="PyPI - Python Version">
<img src="https://img.shields.io/pypi/format/paasify" alt="PyPI - Format">
<img src="https://img.shields.io/pypi/status/paasify" alt="PyPI - Status">
</p>

-------

<p align='center'>
Please :star: this project if like it of if you want to support it!
</p>

<p align='center'>
:warning: This project is currently in alpha stage, use at your own risks! :warning:
</p>

<p align='center'>
Official documentation is available on <a href="https://barbu-it.github.io/paasify/">https://barbu-it.github.io/paasify/</a>.
</p>

-------


Deploy your docker-compose applications with ease and manage your infrastructure as code!

Paasify is a Python tool that will help you to deploy large collections of `docker-compose.yml` files. It's an thin overlay to the `docker compose` command
and it will generate the `docker-compose.yml` you need. It provides some ways to fetch Apps collections, to deploy them and then ensure their state
can be committed into version control.


From an high level perspective, this looks like:

<p align='center'>
<img src="docs/src/static/overview.svg" alt="Overview">
</p>


This project try to overstep the missing gap between the docker-compose deployment and static code in way to achieve infrastructure as a code. If you are asking yourself on why you would use Paasify:

* Manage a lot of differents `docker-compose.yml`
* Make your `docker-compose.yml` based infrastructure [DRY](https://en.wikipedia.org/wiki/Don%27t_repeat_yourself)
* Write large collections of `docker-compose.yml` apps once, deploy them many times
* Integrate your apps into other services, like you can automagically add Traefik labels to your containers
* Deploy apps in a sequential way
* Commit your infrastructure configuration into git


## :memo: Table of Content


  * [Quickstart](#quickstart)
    + [Installation with pip](#installation-with-pip)
    + [Installation with docker](#installation-with-docker)
    + [Example project: Wordpress](#example-project-wordpress)
    + [Demo](#demo)
  * [Overview](#overview)
    + [Features](#features)
    + [Documentation](#documentation)
    + [Requirements](#requirements)
    + [Environment Variables](#environment-variables)
  * [Getting help](#getting-help)
    + [Known issues](#known-issues)
    + [FAQ](#faq)
    + [Support](#support)
    + [Feedback](#feedback)
  * [Develop](#develop)
  * [Project information](#project-information)


## :fire: Quickstart

There are different ways to install Paasify:

* [Installation with pip](#installation-with-pip): This is the recommended installation method for people who wants to try and/or develop infrastructure.
* [Installation with docker](#installation-with-docker): Docker installation is more recommended for production environment. (WIP)
* [Installation with git](https://barbu-it.github.io/paasify/develop/install/): If you want to improve or contribute to Paasify itself.


### Installation with pip

Install Paasify with pip. You may eventually install paasify in its own
Python VirtualEnv, please adapt your commands, but for most people:

```bash
pip install paasify
```

You can check paasify is correctly installed by running the command:
```
paasify --help
```


### Example project: Wordpress

You need to have git and a running docker daemon. See requirements section for further
details.

Let's try to deploy a simple Wordpress instance with Paasify. It consists in deploying
a proxy, for managing incoming traffic (we uses Traefik here), a dashboard and
the Worpress instance. To deploy a such project:

```bash
git clone https://github.com/barbu-it/paasify-example-wordpress.git wordpress
cd wordpress
paasify src install
paasify apply
```

Then you can visit: [http://home.localhost](). Of course you can manage your own domains and manage SSL
with let's encrypt. You can virtually add and tweak other applications. To have an idea of what app
you can install, please checkout official collections:

* [barbu-it/paasify-collection-community](https://github.com/barbu-it/paasify-collection-community): Apps provided for and by the community
* [barbu-it/paasify-collection-infra](https://github.com/barbu-it/paasify-collection-infra): Dev et devops oriented Apps

You can also find community collections in github, with the [#paasify-collection](https://github.com/barbu-it/paasify-example-wordpress/search?q=%23paasify-collection) tag.


## :sparkles: Overview

### Features

- Only use the classical syntax of docker compose
- Allow to use any app without effort
- Transform your own applications into collection, and publish them as git repositories
- Allow to centralized collections into git repositories
- Provides a powerful `docker-compose.<TAG>.yml` assemblage
- Provides a simple but powerful variable management and templating model
- Provides jsonnet support for more complex transformations
- Allow to track your infrastructure changes into git

Please check the documentation to know more and see the Road Map below to see what's coming.


### Documentation

The main documentation website is at [https://barbu-it.github.io/paasify/](https://barbu-it.github.io/paasify/).

### Requirements

The following system requirements are:

* Linux x86 based OS (not tested yet on other platforms than Linux so far)
* `docker`
* `docker compose` or `docker-compose`
* `jq`

For development:

* [git](https://git-scm.com/)
* [poetry](https://python-poetry.org/)
* [task](https://taskfile.dev/)

### Environment Variables

You may use the following environment variables to adjust paasify behavior:

`PAASIFY_DEBUG=false`: Show extra log levels if set to `true`

`PAASIFY_TRACE=false`: Show python traces if set to `true`

## :question: Getting help

### Known issues

* Paasify is still at this alpha stage, and not recommended (yet) for production.
* Paasify has only been tested on Linux, more platform *may* come later.
* Paasify heavily use the usage of docker labels, so deploying in an existing infrastructure may lead to conflicts.



### FAQ

#### Does paasify involve any long running services ?

Nope, Paasify build your `docker-compose.yml` files and do a `docker compose up`. It's a simple CLI program that will super-charge your `docker compose` commands.

#### Is there a web UI for deployments ?

Nope, the intended audience of this tool is people who want to do code as infrastructure. It may be the purpose of another project tho.

#### Is it possible to have it in Go?

Go is a pretty good language for this kind of tool, however the author does not known Go, so it's too late now. Use the docker image to get a no install setup.


### Support

There is no support outside of community support at this stage of the project. The project is still considered as immature, getting into the project as the date of today may still require you to be comfortable with programming.


### Feedback

If you have any feedback, please open an issue.


## :pray: Develop

Here are the basic step to hack into paasify code. A more complete guide is available in the documentation.

### Installation with git

Clone the project

```bash
  git clone https://github.com/barbu-it/paasify
```

Go to the project directory

```bash
  cd paasify
```

Install dependencies

```bash
  task install
```


### Running Tests

To run tests, run the following command

```bash
  task run_tests
```

Run the quality suite

```bash
  task run_qa
```

### Contributing

Contributions are always welcome!

See `contributing.md` for ways to get started.

Please adhere to this project's `code of conduct`.


## :earth_africa: Project information

### Roadmap

- Volume and secret management
- Docker Swarm support


### License

[GNU General Public License v3.0](LICENSE.txt)

### Authors

This project is brought to you thanks to Barbu-IT.

- [@mrjk](https://www.github.com/mrjk)


### Used By

This project is used by the following companies:

- Barbu-IT


### Related

Here are some related projects:

* [Dokku](https://github.com/dokku/dokku)


### Support this project

You can :star: this project, contribute or donate to original author [@mrjk](https://www.github.com/mrjk):

* Bitcoin: `bc1qxdtn24vl9n8e04992dwcq3pdumes0l2dqardvh`
