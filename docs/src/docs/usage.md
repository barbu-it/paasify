# Usage

Paasify was designed for devops in mind. So it features some default and sentive behavior in way to improve working with paasify.

## Relative vs absolute path management

Depending how you call Paasify, it will use absolute or relative path. Paasify will follow the way it's configuration has been provided:


| Command               | Relative                               | Absolute                              |
|-----------------------|----------------------------------------|---------------------------------------|
| From inside the repo  | `paasify info`                         | `paasify -c $PWD info`                |
| From outside the repo | `paasify -c ../../projects/prj1/ info` | `paasify -c /srv/projects/prj1/ info` |


## Stack selection and working directory

All stacks related commands permit to restrict action only on a set of stacks. By default, paasify works on all stack, by the order defined in the paasify configuration.

```console
# By default all stack are selected, in the order defined in the conf
$ paasify up

# The only exception is down, which do the same but in a reversed order
$ paasify down

# We can also specifically select stacks
$ paasify down wordpress

# Or many, with coma separated
$ paasify up wordpress,phpmyadmin

# And the down argument will automatically start by the end as well
$ paasify down traefik,phpmyadmin

# Sugar for the last one, you can use path(s) as well
$ paasify up ../traefik
```

The command line is contextualized depending your current working directory, `$PWD`. First, Paasify
will try to find the closest `paasify.yml` file in parent directories. If a project is found, it auto loads it. If your `$PWD` is under a stack folder, then paasify will work by default with this stack. Get back to the root of your project to work with all stacks, or names explicitely the stacks you want to work with as argument:

``` console
# For a given project:
$ tree $PWD
.
|-- paasify.yml
|-- traefik
|   `-- docker-compose.run.yml
|-- wireguard
|   `-- docker-compose.run.yml
`-- wordpress
    `-- docker-compose.run.yml

# At the root
$ paasify vars --vars app_fqdn
  NOTICE: Get stack vars: traefik
{'app_fqdn': 'traefik.example.net'}
  NOTICE: Get stack vars: wireguard
{'app_fqdn': 'wireguard.example.net'}
  NOTICE: Get stack vars: wordpress
{'app_fqdn': 'blog.example.net'}

# But if you move to a subdir
$ cd traefik

# Paasify now only works on traefik
$ paasify vars --vars app_fqdn
  NOTICE: Get stack vars: traefik
{'app_fqdn': 'traefik.example.net'}

# To work on other stacks
$ paasify vars --vars app_fqdn wordpress
  NOTICE: Get stack vars: wordpress
{'app_fqdn': 'blog.example.net'}

# Or even use combos
$ paasify vars --vars app_fqdn wordpress,wireguard
  NOTICE: Get stack vars: wireguard
{'app_fqdn': 'wireguard.example.net'}
  NOTICE: Get stack vars: wordpress
{'app_fqdn': 'blog.example.net'}

```

This behavior is similar for both CLI and python library.

## Troubleshooting

Paasify comes with configurable logging and helpers to understand and troubleshoot issues with your project. Paasify globally accepts these debug flags. Log levels above EXEC may leak sensitive information in logs:

* `-v`: Show files access (INFO)
* `-vv`: Show sub command execution (EXEC)
* `-vvv`: Show detailed logs (DEBUG)
* `-vvvv`: Show internal logs (TRACE)
* `-vvvvv`: Dump payloads in logs (TRACE)

Some commands also provides an `--explain` flag, that show a comprehensive view of the internal state of Paasify while it run.

Also, there is a `--trace` flag, that will slightly modify log output format and display any python trace in case of error. This is most useful for debugging Paasify itself than for a daily usage.
