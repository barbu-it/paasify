# Example App

This is an example app.

## App file structure

An application is composed of:

* `docker-compose.yml`: (mendatory) The minimal docker-compose that provide an usable app you can do
* `docker-compose.<TAG>.yml`: Extra to configuration to merge when enabled
* `<TAG>.jsonnet`: A jsonnet tag that can be called
* `vars.yml`: Default app variables

### docker-compose.yml

A very minimal app would have the following `docker-compose.yml`:

```
services:
  default:
    image: alpine
    image: ${app_image:-alpine}
```

What you should never do:

* assign `ports` to services
* use hardcoded names (services, networks), use variables instead


A more real case would looks like:

```
```

### vars.yml

A typical `vars.yml` looks like:

```
app_port: 8080
app_desc: dnsmasq web ui

authelia_jwt_secret: CHANGEME
authelia_session_secret: CHANGEME
authelia_storage_encryption_key: CHANGEME
app_description: A painless self-hosted Git service
app_image: lscr.io/linuxserver/librespeed
app_image_version: 5.2.5
homepage_icon: librespeed
app_description: Free and Open Source Speedtest. No Flash, No Java, No Websocket, No Bullshit
app_network_name: $net_ostorage
app_network_name: ${net_ldap}
app_port: 3001
wg_peers: user1,user2,user3
wg_peerdns: auto
wg_internal_subnet: 10.29.30.0
wg_allowed_ips: 10.6.1.0/25,10.5.1.0/26,10.4.1.0/25,10.3.1.0/25,10.2.1.0/25,172.16.1.0/25


```
