# Paasify Stack configuration

**Title:** Paasify Stack configuration

|              |                   |
| ------------ | ----------------- |
| **Type**     | `array of object` |
| **Required** | No                |
| **Default**  | `[]`              |

**Description:** Stacks are defined in a list of objects

|                      | Array restrictions |
| -------------------- | ------------------ |
| **Min items**        | N/A                |
| **Max items**        | N/A                |
| **Items unicity**    | False              |
| **Additional items** | False              |
| **Tuple validation** | See below          |

| Each item of this array must be        | Description |
| -------------------------------------- | ----------- |
| [Paasify Stack configuration](#_items) | -           |

## <a name="autogenerated_heading_2"></a>items

**Title:** Paasify Stack configuration

|                           |                                                                                                           |
| ------------------------- | --------------------------------------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                                                  |
| **Required**              | No                                                                                                        |
| **Additional properties** | [[Not allowed]](# "Additional Properties not allowed.")                                                   |
| **Default**               | `{"path": null, "name": null, "app": null, "tags": [], "tags_suffix": [], "tags_prefix": [], "vars": []}` |

| Property                              | Pattern | Type        | Deprecated | Definition | Title/Description                |
| ------------------------------------- | ------- | ----------- | ---------- | ---------- | -------------------------------- |
| - [name](#_items_name )               | No      | string      | No         | -          | -                                |
| - [path](#_items_path )               | No      | string      | No         | -          | -                                |
| - [app](#_items_app )                 | No      | string      | No         | -          | -                                |
| - [tags](#_items_tags )               | No      | Combination | No         | -          | Paasify Stack Tags configuration |
| - [tags_prefix](#_items_tags_prefix ) | No      | Combination | No         | -          | Paasify Stack Tags configuration |
| - [tags_suffix](#_items_tags_suffix ) | No      | Combination | No         | -          | Paasify Stack Tags configuration |
| - [vars](#_items_vars )               | No      | Combination | No         | -          | Environment configuration        |

### <a name="_items_name"></a>Property `name`

|              |          |
| ------------ | -------- |
| **Type**     | `string` |
| **Required** | No       |

### <a name="_items_path"></a>Property `path`

|              |          |
| ------------ | -------- |
| **Type**     | `string` |
| **Required** | No       |

### <a name="_items_app"></a>Property `app`

|              |          |
| ------------ | -------- |
| **Type**     | `string` |
| **Required** | No       |

### <a name="_items_tags"></a>Property `tags`

**Title:** Paasify Stack Tags configuration

|              |             |
| ------------ | ----------- |
| **Type**     | `combining` |
| **Required** | No          |

**Description:** Determine a list of tags to apply.

| One of(Option)                        |
| ------------------------------------- |
| [List of tags](#_items_tags_oneOf_i0) |
| [Unset](#_items_tags_oneOf_i1)        |

#### <a name="_items_tags_oneOf_i0"></a>Property `None`

**Title:** List of tags

|              |         |
| ------------ | ------- |
| **Type**     | `array` |
| **Required** | No      |
| **Default**  | `[]`    |

**Description:** Define a list of tags. You can interact in few ways with tags. Tags can support boths syntaxes at the same time.

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

|                      | Array restrictions |
| -------------------- | ------------------ |
| **Min items**        | N/A                |
| **Max items**        | N/A                |
| **Items unicity**    | False              |
| **Additional items** | False              |
| **Tuple validation** | N/A                |

#### <a name="_items_tags_oneOf_i1"></a>Property `None`

**Title:** Unset

|              |        |
| ------------ | ------ |
| **Type**     | `null` |
| **Required** | No     |
| **Default**  | `null` |

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

### <a name="_items_tags_prefix"></a>Property `tags_prefix`

**Title:** Paasify Stack Tags configuration

|              |             |
| ------------ | ----------- |
| **Type**     | `combining` |
| **Required** | No          |

**Description:** Determine a list of tags to apply.

| One of(Option)                               |
| -------------------------------------------- |
| [List of tags](#_items_tags_prefix_oneOf_i0) |
| [Unset](#_items_tags_prefix_oneOf_i1)        |

#### <a name="_items_tags_prefix_oneOf_i0"></a>Property `None`

**Title:** List of tags

|              |         |
| ------------ | ------- |
| **Type**     | `array` |
| **Required** | No      |
| **Default**  | `[]`    |

**Description:** Define a list of tags. You can interact in few ways with tags. Tags can support boths syntaxes at the same time.

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

|                      | Array restrictions |
| -------------------- | ------------------ |
| **Min items**        | N/A                |
| **Max items**        | N/A                |
| **Items unicity**    | False              |
| **Additional items** | False              |
| **Tuple validation** | N/A                |

#### <a name="_items_tags_prefix_oneOf_i1"></a>Property `None`

**Title:** Unset

|              |        |
| ------------ | ------ |
| **Type**     | `null` |
| **Required** | No     |
| **Default**  | `null` |

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

### <a name="_items_tags_suffix"></a>Property `tags_suffix`

**Title:** Paasify Stack Tags configuration

|              |             |
| ------------ | ----------- |
| **Type**     | `combining` |
| **Required** | No          |

**Description:** Determine a list of tags to apply.

| One of(Option)                               |
| -------------------------------------------- |
| [List of tags](#_items_tags_suffix_oneOf_i0) |
| [Unset](#_items_tags_suffix_oneOf_i1)        |

#### <a name="_items_tags_suffix_oneOf_i0"></a>Property `None`

**Title:** List of tags

|              |         |
| ------------ | ------- |
| **Type**     | `array` |
| **Required** | No      |
| **Default**  | `[]`    |

**Description:** Define a list of tags. You can interact in few ways with tags. Tags can support boths syntaxes at the same time.

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

|                      | Array restrictions |
| -------------------- | ------------------ |
| **Min items**        | N/A                |
| **Max items**        | N/A                |
| **Items unicity**    | False              |
| **Additional items** | False              |
| **Tuple validation** | N/A                |

#### <a name="_items_tags_suffix_oneOf_i1"></a>Property `None`

**Title:** Unset

|              |        |
| ------------ | ------ |
| **Type**     | `null` |
| **Required** | No     |
| **Default**  | `null` |

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

### <a name="_items_vars"></a>Property `vars`

**Title:** Environment configuration

|                           |                                                                           |
| ------------------------- | ------------------------------------------------------------------------- |
| **Type**                  | `combining`                                                               |
| **Required**              | No                                                                        |
| **Additional properties** | [[Any type: allowed]](# "Additional Properties of any type are allowed.") |

**Description:** Environment configuration. Paasify leave two choices for the configuration, either use the native dict configuration or use the docker-compatible format

| One of(Option)                                              |
| ----------------------------------------------------------- |
| [Env configuration as list](#_items_vars_oneOf_i0)          |
| [Env configuration as dict (Compat)](#_items_vars_oneOf_i1) |
| [Unset](#_items_vars_oneOf_i2)                              |

#### <a name="_items_vars_oneOf_i0"></a>Property `None`

**Title:** Env configuration as list

|              |         |
| ------------ | ------- |
| **Type**     | `array` |
| **Required** | No      |
| **Default**  | `[]`    |

**Description:** Configure variables as a list. This is the recommended way asit preserves the variable parsing order, useful for templating. This format allow multiple configuration format.

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

|                      | Array restrictions |
| -------------------- | ------------------ |
| **Min items**        | N/A                |
| **Max items**        | N/A                |
| **Items unicity**    | False              |
| **Additional items** | False              |
| **Tuple validation** | N/A                |

#### <a name="_items_vars_oneOf_i1"></a>Property `None`

**Title:** Env configuration as dict (Compat)

|                           |                                                                                                                                |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| **Type**                  | `object`                                                                                                                       |
| **Required**              | No                                                                                                                             |
| **Additional properties** | [[Should-conform]](#_items_vars_oneOf_i1_additionalProperties "Each additional property must conform to the following schema") |
| **Default**               | `{}`                                                                                                                           |

**Description:** Configure variables as a dict. This option is only proposed for compatibility reasons. It does not preserve the order of the variables.

**Example:**

```yaml
env:
  MYSQL_ADMIN_USER: MyUser
  MYSQL_ADMIN_DB: MyDB
  MYSQL_ENABLE_BACKUP: true
  MYSQL_BACKUPS_NODES: 3
  MYSQL_NODE_REPLICA: null

```

| Property                                                              | Pattern | Type   | Deprecated | Definition | Title/Description                |
| --------------------------------------------------------------------- | ------- | ------ | ---------- | ---------- | -------------------------------- |
| - [additionalProperties](#_items_vars_oneOf_i1_additionalProperties ) | No      | object | No         | -          | Variable definition as key/value |

##### <a name="_items_vars_oneOf_i1_additionalProperties"></a>Property `additionalProperties`

**Title:** Variable definition as key/value

|                           |                                                                           |
| ------------------------- | ------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                  |
| **Required**              | No                                                                        |
| **Additional properties** | [[Any type: allowed]](# "Additional Properties of any type are allowed.") |

**Description:** Simple key value variable declaration, under the form of: {KEY: VALUE}. This does preserve value type.

| Property                                                                           | Pattern | Type        | Deprecated | Definition | Title/Description     |
| ---------------------------------------------------------------------------------- | ------- | ----------- | ---------- | ---------- | --------------------- |
| - [^[A-Za-z_][A-Za-z0-9_]*$](#_items_vars_oneOf_i1_additionalProperties_pattern1 ) | Yes     | Combination | No         | -          | Environment Key value |

##### <a name="_items_vars_oneOf_i1_additionalProperties_pattern1"></a>Pattern Property `^[A-Za-z_][A-Za-z0-9_]*$`
> All properties whose name matches the regular expression
```^[A-Za-z_][A-Za-z0-9_]*$``` ([Test](https://regex101.com/?regex=%5E%5BA-Za-z_%5D%5BA-Za-z0-9_%5D%2A%24))
must respect the following conditions

**Title:** Environment Key value

|                           |                                                                           |
| ------------------------- | ------------------------------------------------------------------------- |
| **Type**                  | `combining`                                                               |
| **Required**              | No                                                                        |
| **Additional properties** | [[Any type: allowed]](# "Additional Properties of any type are allowed.") |

**Description:** Value must be serializable type

| One of(Option)                                                             |
| -------------------------------------------------------------------------- |
| [As string](#_items_vars_oneOf_i1_additionalProperties_pattern1_oneOf_i0)  |
| [As boolean](#_items_vars_oneOf_i1_additionalProperties_pattern1_oneOf_i1) |
| [As integer](#_items_vars_oneOf_i1_additionalProperties_pattern1_oneOf_i2) |
| [As null](#_items_vars_oneOf_i1_additionalProperties_pattern1_oneOf_i3)    |

##### <a name="_items_vars_oneOf_i1_additionalProperties_pattern1_oneOf_i0"></a>Property `None`

**Title:** As string

|              |          |
| ------------ | -------- |
| **Type**     | `string` |
| **Required** | No       |

##### <a name="_items_vars_oneOf_i1_additionalProperties_pattern1_oneOf_i1"></a>Property `None`

**Title:** As boolean

|              |           |
| ------------ | --------- |
| **Type**     | `boolean` |
| **Required** | No        |

##### <a name="_items_vars_oneOf_i1_additionalProperties_pattern1_oneOf_i2"></a>Property `None`

**Title:** As integer

|              |           |
| ------------ | --------- |
| **Type**     | `integer` |
| **Required** | No        |

##### <a name="_items_vars_oneOf_i1_additionalProperties_pattern1_oneOf_i3"></a>Property `None`

**Title:** As null

|              |        |
| ------------ | ------ |
| **Type**     | `null` |
| **Required** | No     |

**Description:** If set to null, this will remove variable

#### <a name="_items_vars_oneOf_i2"></a>Property `None`

**Title:** Unset

|              |        |
| ------------ | ------ |
| **Type**     | `null` |
| **Required** | No     |
| **Default**  | `null` |

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

----------------------------------------------------------------------------------------------------------------------------
Generated using [json-schema-for-humans](https://github.com/coveooss/json-schema-for-humans)
