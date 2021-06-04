## Simple-Odata

A simple service odata service provider.

[![SesamCommunity CI&CD](https://github.com/sesam-community/simple-odata/actions/workflows/sesam-community-ci-cd.yml/badge.svg)](https://github.com/sesam-community/simple-odata/actions/workflows/sesam-community-ci-cd.yml)

### Environment variables:

`base_url` - the base url of the odata API service.

`value_field` - the name of the field containing the values, default value: value.

`page_size` - the number of entities fetched pr. page, default value: 1000.

`page_size_parameter` - name of the parameter that sets the number of entities returned pr page.

`page_parameter` - name of the parameter that sets which page to return.

`use_page_as_counter` - when set to true, the service will send the number of the page as the value to the page_parameter. When set to false, the service will send the current count of fetched entities to the page_parameter. Default value: false.

`use_paging` - set if paging should be used or not, default value: false.

`since_property` - set this value to the name of property for the since value if continuation support is enabled for the source.

### Querystring restricted parameters:

`_key` - can be used to override the value of the 'value_field' parameters. This is useful for services where the entities returned resides in a property that is not constant in the API.

`_paging` - can be used to override the value of the 'use_paging' parameters.

### Example system config:

```json
{
  "_id": "a-simple-odata-system",
  "type": "system:microservice",
  "docker": {
    "environment": {
      "base_url": "https://base.url.to.odata.service/"
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