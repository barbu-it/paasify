# Paasify

**Title:** Paasify

| Type                      | `object`                                                |
| ------------------------- | ------------------------------------------------------- |
| **Additional properties** | [[Not allowed]](# "Additional Properties not allowed.") |
| **Default**               | `{}`                                                    |

**Description:** Main paasify project settings. This defines the format of `paasify.yml`.

| Property               | Pattern | Type   | Deprecated | Definition        | Title/Description                                                                    |
| ---------------------- | ------- | ------ | ---------- | ----------------- | ------------------------------------------------------------------------------------ |
| - [config](#config )   | No      | object | No         | In #/$defs/Config | Configure main project settings. It provides global settings but also defaults v ... |
| - [sources](#sources ) | No      | object | No         | -                 | -                                                                                    |
| - [stacks](#stacks )   | No      | object | No         | -                 | -                                                                                    |

## <a name="config"></a>[Optional] Property `config`

| Type                      | `object`                                                                  |
| ------------------------- | ------------------------------------------------------------------------- |
| **Additional properties** | [[Any type: allowed]](# "Additional Properties of any type are allowed.") |
| **Defined in**            | #/$defs/Config                                                            |

**Description:** Configure main project settings. It provides global settings but also defaults vars and tags for all stacks.

| One of(Option)                            |
| ----------------------------------------- |
| [Project configuration](#config_oneOf_i0) |
| [Empty](#config_oneOf_i1)                 |

### <a name="config_oneOf_i0"></a>Property `None`

**Title:** Project configuration

| Type                      | `object`                                                |
| ------------------------- | ------------------------------------------------------- |
| **Additional properties** | [[Not allowed]](# "Additional Properties not allowed.") |
| **Default**               | `{}`                                                    |

**Description:** Configure project as a dict value. Most of these settings are overridable via environment vars.

| Property                                       | Pattern | Type        | Deprecated | Definition | Title/Description                |
| ---------------------------------------------- | ------- | ----------- | ---------- | ---------- | -------------------------------- |
| - [namespace](#config_oneOf_i0_namespace )     | No      | Combination | No         | -          | Project namespace                |
| - [vars](#config_oneOf_i0_vars )               | No      | Combination | No         | -          | Environment configuration        |
| - [tags](#config_oneOf_i0_tags )               | No      | Combination | No         | -          | Paasify Stack Tags configuration |
| - [tags_suffix](#config_oneOf_i0_tags_suffix ) | No      | Combination | No         | -          | Paasify Stack Tags configuration |
| - [tags_prefix](#config_oneOf_i0_tags_prefix ) | No      | Combination | No         | -          | Paasify Stack Tags configuration |

**Example:** 

```yaml
config:
  namespace: my_ns1
  vars:
  - my_var1: my_value1
  tags:
  - tag1
  - tag2

```

#### <a name="config_oneOf_i0_namespace"></a>Property `namespace`

**Title:** Project namespace

| Type                      | `combining`                                                               |
| ------------------------- | ------------------------------------------------------------------------- |
| **Additional properties** | [[Any type: allowed]](# "Additional Properties of any type are allowed.") |

**Description:** Name of the project namespace. If not set, defaulted to directory name

| One of(Option)                                |
| --------------------------------------------- |
| [None](#config_oneOf_i0_namespace_oneOf_i0)   |
| [String](#config_oneOf_i0_namespace_oneOf_i1) |

##### <a name="config_oneOf_i0_namespace_oneOf_i0"></a>Property `None`

**Title:** None

| Type | `null` |
| ---- | ------ |

**Description:** Defaulted by the project dir name

##### <a name="config_oneOf_i0_namespace_oneOf_i1"></a>Property `None`

**Title:** String

| Type | `string` |
| ---- | -------- |

**Description:** Custom namespace name string

#### <a name="config_oneOf_i0_vars"></a>Property `vars`

**Title:** Environment configuration

| Type                      | `combining`                                                               |
| ------------------------- | ------------------------------------------------------------------------- |
| **Additional properties** | [[Any type: allowed]](# "Additional Properties of any type are allowed.") |

**Description:** Environment configuration. Paasify leave two choices for the configuration, either use the native dict configuration or use the docker-compatible format

| One of(Option)                                                       |
| -------------------------------------------------------------------- |
| [Env configuration as list](#config_oneOf_i0_vars_oneOf_i0)          |
| [Env configuration as dict (Compat)](#config_oneOf_i0_vars_oneOf_i1) |
| [Unset](#config_oneOf_i0_vars_oneOf_i2)                              |

##### <a name="config_oneOf_i0_vars_oneOf_i0"></a>Property `None`

**Title:** Env configuration as list

| Type        | `array` |
| ----------- | ------- |
| **Default** | `[]`    |

**Description:** Configure variables as a list. This is the recommended way asit preserves the variable parsing order, useful for templating. This format allow multiple configuration format.

|                      | Array restrictions |
| -------------------- | ------------------ |
| **Min items**        | N/A                |
| **Max items**        | N/A                |
| **Items unicity**    | False              |
| **Additional items** | False              |
| **Tuple validation** | N/A                |

**Example:** 

```yaml
env:
- MYSQL_ADMIN_USER: MyUser
- MYSQL_ADMIN_DB: MyDB
- MYSQL_ENABLE_BACKUP: true
- MYSQL_BACKUPS_NODES: 3
- MYSQL_NODE_REPLICA: null
- MYSQL_WELCOME_STRING=Is alway a string

```

##### <a name="config_oneOf_i0_vars_oneOf_i1"></a>Property `None`

**Title:** Env configuration as dict (Compat)

| Type                      | `object`                                                                                                                                |
| ------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| **Additional properties** | [[Should-conform]](#config_oneOf_i0_vars_oneOf_i1_additionalProperties "Each additional property must conform to the following schema") |
| **Default**               | `{}`                                                                                                                                    |

**Description:** Configure variables as a dict. This option is only proposed for compatibility reasons. It does not preserve the order of the variables.

| Property                                                                       | Pattern | Type   | Deprecated | Definition | Title/Description                |
| ------------------------------------------------------------------------------ | ------- | ------ | ---------- | ---------- | -------------------------------- |
| - [additionalProperties](#config_oneOf_i0_vars_oneOf_i1_additionalProperties ) | No      | object | No         | -          | Variable definition as key/value |

**Example:** 

```yaml
env:
  MYSQL_ADMIN_USER: MyUser
  MYSQL_ADMIN_DB: MyDB
  MYSQL_ENABLE_BACKUP: true
  MYSQL_BACKUPS_NODES: 3
  MYSQL_NODE_REPLICA: null

```

##### <a name="config_oneOf_i0_vars_oneOf_i1_additionalProperties"></a>Property `additionalProperties`

**Title:** Variable definition as key/value

| Type                      | `object`                                                                  |
| ------------------------- | ------------------------------------------------------------------------- |
| **Additional properties** | [[Any type: allowed]](# "Additional Properties of any type are allowed.") |

**Description:** Simple key value variable declaration, under the form of: {KEY: VALUE}. This does preserve value type.

| Property                                                                                    | Pattern | Type        | Deprecated | Definition | Title/Description     |
| ------------------------------------------------------------------------------------------- | ------- | ----------- | ---------- | ---------- | --------------------- |
| - [^[A-Za-z_][A-Za-z0-9_]*$](#config_oneOf_i0_vars_oneOf_i1_additionalProperties_pattern1 ) | Yes     | Combination | No         | -          | Environment Key value |

##### <a name="config_oneOf_i0_vars_oneOf_i1_additionalProperties_pattern1"></a>Pattern Property `^[A-Za-z_][A-Za-z0-9_]*$`
> All properties whose name matches the regular expression
```^[A-Za-z_][A-Za-z0-9_]*$``` ([Test](https://regex101.com/?regex=%5E%5BA-Za-z_%5D%5BA-Za-z0-9_%5D%2A%24))
must respect the following conditions

**Title:** Environment Key value

| Type                      | `combining`                                                               |
| ------------------------- | ------------------------------------------------------------------------- |
| **Additional properties** | [[Any type: allowed]](# "Additional Properties of any type are allowed.") |

**Description:** Value must be serializable type

| One of(Option)                                                                      |
| ----------------------------------------------------------------------------------- |
| [As string](#config_oneOf_i0_vars_oneOf_i1_additionalProperties_pattern1_oneOf_i0)  |
| [As boolean](#config_oneOf_i0_vars_oneOf_i1_additionalProperties_pattern1_oneOf_i1) |
| [As integer](#config_oneOf_i0_vars_oneOf_i1_additionalProperties_pattern1_oneOf_i2) |
| [As null](#config_oneOf_i0_vars_oneOf_i1_additionalProperties_pattern1_oneOf_i3)    |

##### <a name="config_oneOf_i0_vars_oneOf_i1_additionalProperties_pattern1_oneOf_i0"></a>Property `None`

**Title:** As string

| Type | `string` |
| ---- | -------- |

##### <a name="config_oneOf_i0_vars_oneOf_i1_additionalProperties_pattern1_oneOf_i1"></a>Property `None`

**Title:** As boolean

| Type | `boolean` |
| ---- | --------- |

##### <a name="config_oneOf_i0_vars_oneOf_i1_additionalProperties_pattern1_oneOf_i2"></a>Property `None`

**Title:** As integer

| Type | `integer` |
| ---- | --------- |

##### <a name="config_oneOf_i0_vars_oneOf_i1_additionalProperties_pattern1_oneOf_i3"></a>Property `None`

**Title:** As null

| Type | `null` |
| ---- | ------ |

**Description:** If set to null, this will remove variable

##### <a name="config_oneOf_i0_vars_oneOf_i2"></a>Property `None`

**Title:** Unset

| Type        | `null` |
| ----------- | ------ |
| **Default** | `null` |

**Description:** Do not define any vars

**Examples:** 

```yaml
env: null

```

```yaml
env: []

```

```yaml
env: {}

```

#### <a name="config_oneOf_i0_tags"></a>Property `tags`

**Title:** Paasify Stack Tags configuration

| Type | `combining` |
| ---- | ----------- |

**Description:** Determine a list of tags to apply.

| One of(Option)                                 |
| ---------------------------------------------- |
| [List of tags](#config_oneOf_i0_tags_oneOf_i0) |
| [Unset](#config_oneOf_i0_tags_oneOf_i1)        |

##### <a name="config_oneOf_i0_tags_oneOf_i0"></a>Property `None`

**Title:** List of tags

| Type        | `array` |
| ----------- | ------- |
| **Default** | `[]`    |

**Description:** Define a list of tags. You can interact in few ways with tags. Tags can support boths syntaxes at the same time.

|                      | Array restrictions |
| -------------------- | ------------------ |
| **Min items**        | N/A                |
| **Max items**        | N/A                |
| **Items unicity**    | False              |
| **Additional items** | False              |
| **Tuple validation** | N/A                |

**Example:** 

```yaml
tags:
- my_tagg
- ~my_prefix_tag
- my_collection:my_prefix_tag
- other_tag:
    specific_conf: val1
- my_collection:another_tag: null
- ~ignore_this_tag:
    specific_conf: val1

```

##### <a name="config_oneOf_i0_tags_oneOf_i1"></a>Property `None`

**Title:** Unset

| Type        | `null` |
| ----------- | ------ |
| **Default** | `null` |

**Description:** Do not declare any tags

**Example:** 

```yaml
tags: null

```

|                      | Array restrictions |
| -------------------- | ------------------ |
| **Min items**        | N/A                |
| **Max items**        | N/A                |
| **Items unicity**    | False              |
| **Additional items** | False              |
| **Tuple validation** | N/A                |

#### <a name="config_oneOf_i0_tags_suffix"></a>Property `tags_suffix`

**Title:** Paasify Stack Tags configuration

| Type | `combining` |
| ---- | ----------- |

**Description:** Determine a list of tags to apply.

| One of(Option)                                        |
| ----------------------------------------------------- |
| [List of tags](#config_oneOf_i0_tags_suffix_oneOf_i0) |
| [Unset](#config_oneOf_i0_tags_suffix_oneOf_i1)        |

##### <a name="config_oneOf_i0_tags_suffix_oneOf_i0"></a>Property `None`

**Title:** List of tags

| Type        | `array` |
| ----------- | ------- |
| **Default** | `[]`    |

**Description:** Define a list of tags. You can interact in few ways with tags. Tags can support boths syntaxes at the same time.

|                      | Array restrictions |
| -------------------- | ------------------ |
| **Min items**        | N/A                |
| **Max items**        | N/A                |
| **Items unicity**    | False              |
| **Additional items** | False              |
| **Tuple validation** | N/A                |

**Example:** 

```yaml
tags:
- my_tagg
- ~my_prefix_tag
- my_collection:my_prefix_tag
- other_tag:
    specific_conf: val1
- my_collection:another_tag: null
- ~ignore_this_tag:
    specific_conf: val1

```

##### <a name="config_oneOf_i0_tags_suffix_oneOf_i1"></a>Property `None`

**Title:** Unset

| Type        | `null` |
| ----------- | ------ |
| **Default** | `null` |

**Description:** Do not declare any tags

**Example:** 

```yaml
tags: null

```

|                      | Array restrictions |
| -------------------- | ------------------ |
| **Min items**        | N/A                |
| **Max items**        | N/A                |
| **Items unicity**    | False              |
| **Additional items** | False              |
| **Tuple validation** | N/A                |

#### <a name="config_oneOf_i0_tags_prefix"></a>Property `tags_prefix`

**Title:** Paasify Stack Tags configuration

| Type | `combining` |
| ---- | ----------- |

**Description:** Determine a list of tags to apply.

| One of(Option)                                        |
| ----------------------------------------------------- |
| [List of tags](#config_oneOf_i0_tags_prefix_oneOf_i0) |
| [Unset](#config_oneOf_i0_tags_prefix_oneOf_i1)        |

##### <a name="config_oneOf_i0_tags_prefix_oneOf_i0"></a>Property `None`

**Title:** List of tags

| Type        | `array` |
| ----------- | ------- |
| **Default** | `[]`    |

**Description:** Define a list of tags. You can interact in few ways with tags. Tags can support boths syntaxes at the same time.

|                      | Array restrictions |
| -------------------- | ------------------ |
| **Min items**        | N/A                |
| **Max items**        | N/A                |
| **Items unicity**    | False              |
| **Additional items** | False              |
| **Tuple validation** | N/A                |

**Example:** 

```yaml
tags:
- my_tagg
- ~my_prefix_tag
- my_collection:my_prefix_tag
- other_tag:
    specific_conf: val1
- my_collection:another_tag: null
- ~ignore_this_tag:
    specific_conf: val1

```

##### <a name="config_oneOf_i0_tags_prefix_oneOf_i1"></a>Property `None`

**Title:** Unset

| Type        | `null` |
| ----------- | ------ |
| **Default** | `null` |

**Description:** Do not declare any tags

**Example:** 

```yaml
tags: null

```

|                      | Array restrictions |
| -------------------- | ------------------ |
| **Min items**        | N/A                |
| **Max items**        | N/A                |
| **Items unicity**    | False              |
| **Additional items** | False              |
| **Tuple validation** | N/A                |

### <a name="config_oneOf_i1"></a>Property `None`

**Title:** Empty

| Type        | `null` |
| ----------- | ------ |
| **Default** | `null` |

**Description:** Use automatic conf if not set. You can still override conf values with environment vars.

**Examples:** 

```yaml
config: null

```

```yaml
config: {}

```

## <a name="sources"></a>[Optional] Property `sources`

| Type                      | `object`                                                                  |
| ------------------------- | ------------------------------------------------------------------------- |
| **Additional properties** | [[Any type: allowed]](# "Additional Properties of any type are allowed.") |

## <a name="stacks"></a>[Optional] Property `stacks`

| Type                      | `object`                                                                  |
| ------------------------- | ------------------------------------------------------------------------- |
| **Additional properties** | [[Any type: allowed]](# "Additional Properties of any type are allowed.") |

----------------------------------------------------------------------------------------------------------------------------
Generated using [json-schema-for-humans](https://github.com/coveooss/json-schema-for-humans)
