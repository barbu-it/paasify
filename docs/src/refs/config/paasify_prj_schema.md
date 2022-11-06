# Paasify

**Title:** Paasify

| Type                      | `object`                                                |
| ------------------------- | ------------------------------------------------------- |
| **Additional properties** | [[Not allowed]](# "Additional Properties not allowed.") |
| **Default**               | `{}`                                                    |

**Description:** Main paasify project settings. This defines the format of `paasify.yml`.

| Property                  | Pattern | Type   | Deprecated | Definition | Title/Description         |
| ------------------------- | ------- | ------ | ---------- | ---------- | ------------------------- |
| - [config](#config )      | No      | object | No         | -          | See: schema prj_config    |
| - [sources](#sources )    | No      | object | No         | -          | See: schema prj_sources   |
| - [stacks](#stacks )      | No      | array  | No         | -          | See: schema prj_stacks    |
| - [_runtime](#a_runtime ) | No      | object | No         | -          | Project runtime variables |

**Example:** 

```yaml
config:
  tags_prefix:
  - _paasify
  vars:
    app_domain: devbox.192.168.186.129.nip.io
    app_expose_ip: 192.168.186.129
    app_tz: Europe/Paris
    top_var1: My value
    top_var2: TOP VAR1=> ${top_var1}
sources:
- default:
    url: https://github.com/user/docker-compose.git
stacks:
- app: default:traefik
  path: traefik
  tags:
  - ep_http
  - expose_admin
  - debug
  - traefik-svc:
      traefik_net_external: false
      traefik_svc_port: '8080'
- app: default:minio
  env:
  - app_admin_passwd: MY_PASS
  - app_image: quay.io/minio/minio:latest
  tags:
  - traefik-svc:
      traefik_svc_name: minio-api
      traefik_svc_port: 9000
  - traefik-svc:
      traefik_svc_name: minio-console
      traefik_svc_port: 9001
- app: default:authelia
  tags:
  - traefik-svc
- app: default:librespeed
  tags:
  - traefik-svc

```

## <a name="config"></a>[Optional] Property `config`

| Type                      | `object`                                                                  |
| ------------------------- | ------------------------------------------------------------------------- |
| **Additional properties** | [[Any type: allowed]](# "Additional Properties of any type are allowed.") |

**Description:** See: schema prj_config

## <a name="sources"></a>[Optional] Property `sources`

| Type                      | `object`                                                                  |
| ------------------------- | ------------------------------------------------------------------------- |
| **Additional properties** | [[Any type: allowed]](# "Additional Properties of any type are allowed.") |

**Description:** See: schema prj_sources

## <a name="stacks"></a>[Optional] Property `stacks`

| Type | `array` |
| ---- | ------- |

**Description:** See: schema prj_stacks

|                      | Array restrictions |
| -------------------- | ------------------ |
| **Min items**        | N/A                |
| **Max items**        | N/A                |
| **Items unicity**    | False              |
| **Additional items** | False              |
| **Tuple validation** | N/A                |

## <a name="a_runtime"></a>[Optional] Property `_runtime`

**Title:** Project runtime variables

| Type                      | `object`                                                                  |
| ------------------------- | ------------------------------------------------------------------------- |
| **Additional properties** | [[Any type: allowed]](# "Additional Properties of any type are allowed.") |

**Description:** Internal object to pass context variables, internal use only or for troubleshooting purpose

----------------------------------------------------------------------------------------------------------------------------
Generated using [json-schema-for-humans](https://github.com/coveooss/json-schema-for-humans)
