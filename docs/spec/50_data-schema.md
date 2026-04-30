# Data Schema

<!-- The file format is a user-facing contract: users own their files,
     can read, edit, and version them directly. Any correct implementation
     must produce and consume files that conform to this schema. -->

## Vault layout

<!-- Directory structure of a valid vault.
     What files are required, what is optional, what is ignored. -->

```
vault/
  ...
```

## Node file

<!-- One file per node. Naming convention, location, encoding. -->

### Filename

<!-- Format, constraints, what parts are meaningful vs cosmetic. -->

### Fields

<!-- Every field: name, type, required/optional, valid values, default. -->

| Field | Type | Required | Description |
|---|---|---|---|
| ... | ... | ... | ... |

### Example

```yaml
# a minimal valid node file
```

```yaml
# a fully populated node file
```

## Links

<!-- How relationships between nodes are stored.
     Which side stores the link, what is derived, what is never stored. -->

## Vault-level files

<!-- Any files that live at vault root (config, index, etc.)
     or confirmation that there are none. -->

## Validity rules

<!-- What makes a vault valid. Constraints an implementation must enforce or tolerate.
     E.g: what happens with a missing file, a duplicate id, a cycle. -->

- ...
