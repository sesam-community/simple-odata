## Simple-Odata

A simple service odata service provider.

[![SesamCommunity CI&CD](https://github.com/sesam-community/simple-odata/actions/workflows/sesam-community-ci-cd.yml/badge.svg)](https://github.com/sesam-community/simple-odata/actions/workflows/sesam-community-ci-cd.yml)

### Environment variables:

`base_url` - the base url of the odata API service.

`id_attribute` - the name of the property containing the id / _id value for an entity.


### Example system config:

```json
{
  "_id": "a-simple-odata-system",
  "type": "system:microservice",
  "docker": {
    "environment": {
      "base_url": "https://base.url.to.odata.service/",
      "id_attribute": "ID"
    },
    "image": "sesamcommunity/simple-odata:1.0",
    "port": 5001
  }
}

```

### Example pipe using the microservice above

```json
{
  "_id": "a-simple-odata-pipe",
  "type": "pipe",
  "source": {
    "is_chronological": false,
    "is_since_comparable": false,
    "supports_since": false,
    "system": "a-simple-odata-system",
    "type": "json",
    "url": "odata-api-path"
  }
}

```