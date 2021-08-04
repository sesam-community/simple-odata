import ujson
import requests
from flask import Flask, Response, request
import os
import logger
import cherrypy
import json_stream
import json_stream.requests

app = Flask(__name__)
logger = logger.Logger('odata-simple')

url = os.environ.get("base_url")
value_field = os.environ.get("value_field", "value")
page_size = int(os.environ.get("page_size", 1000))
page_size_parameter = os.environ.get("page_size_parameter")
page_parameter = os.environ.get("page_parameter")
use_page_as_counter = os.environ.get("use_page_as_counter", "false").lower() == "true"
use_paging = os.environ.get("use_paging", "false").lower() == "true"
since_property = os.environ.get("since_property")
headers = ujson.loads('{"Content-Type": "application/json"}')
starting_offset = int(os.environ.get("debug_starting_offset", 0))


class BasicUrlSystem:
    def __init__(self, config):
        self._config = config

    def make_session(self):
        session = requests.Session()
        session.headers = self._config["headers"]
        session.verify = True
        return session


session_factory = BasicUrlSystem({"headers": headers})


class DataAccess:

    def __get_all_paged_entities(self, base_url, path, query_string, key):
        logger.info(f"Fetching data from url with paging: {path}")
        request_url = "{0}{1}".format(base_url, path)

        if query_string:
            next_page = "{0}?{1}&{2}={3}".format(request_url, query_string, page_size_parameter,
                                                 page_size)
        else:
            next_page = "{0}?{1}={2}".format(request_url, page_size_parameter, page_size)

        if key is None:
            key = value_field
        entity_count = starting_offset
        page_count = 0
        previous_page = None
        while next_page is not None and next_page != previous_page:
            logger.info(f"Fetching data from url: {next_page}")

            with session_factory.make_session() as s:
                request_data = s.request("GET", next_page, headers=headers)

            if not request_data.ok:
                error_text = f"Unexpected response status code: {request_data.status_code} with response text " \
                    f"{request_data.text}"
                logger.error(error_text)
                raise AssertionError(error_text)

            logger.info(f"Content length: {len(request_data.content)}")
            entities = ujson.loads(request_data.content).get(key)

            if entities is not None:
                for entity in entities:
                    if entity is not None:
                        yield (entity)
            else:
                entities = []
                
            entity_count += len(entities)
            page_count += 1

            logger.info(f"Fetched {len(entities)} entities, total: {entity_count}")

            previous_page = next_page

            if len(entities) == 0 or len(entities) < page_size:
                next_page = None
            else:
                next_page = get_next_url(request_url, entity_count, query_string, page_count)

        logger.info(f"Returning {entity_count} entities from {page_count} pages")

    def __get_all_entities(self, base_url, path, query_string, key):
        logger.info(f"Fetching data from url without paging: {path}")
        request_url = "{0}{1}".format(base_url, path)

        if query_string:
            request_url = "{0}?{1}".format(request_url, query_string)

        if key is None:
            key = value_field

        with session_factory.make_session() as s:
            request_data = s.request("GET", request_url, headers=headers)

        if not request_data.ok:
            error_text = f"Unexpected response status code: {request_data.status_code} with response text " \
                f"{request_data.text}"
            logger.error(error_text)
            raise AssertionError(error_text)

        logger.info(f"Content length: {len(request_data.content)}")
        results = json_stream.load(request_data.json)
        entities = results[key]

        if entities is not None:
            for entity in entities:
                if entity is not None:
                    yield (entity)
        else:
            entities = []

        logger.info(f"Fetched {len(entities)} entities, total: {len(entities)}")

    def get_paged_entities(self, base_url, path, query_string, key):
        return self.__get_all_paged_entities(base_url, path, query_string, key)

    def get_all_entities(self, base_url, path, query_string, key):
        return self.__get_all_entities(base_url, path, query_string, key)


data_access_layer = DataAccess()


def get_next_url(base_url, entity_count, query_string, page_count):
    next_count = entity_count
    if use_page_as_counter:
            next_count = page_count

    if query_string:
        request_url = "{0}?{1}&{2}={3}&{4}={5}".format(base_url, query_string, page_size_parameter, page_size,
                                                       page_parameter, next_count)
    else:
        request_url = "{0}?{1}={2}&{3}={4}".format(base_url, page_size_parameter, page_size,
                                                   page_parameter, next_count)

    return request_url


def stream_json(entities):
    first = True
    yield '['
    if entities is not None:
        for i, row in enumerate(entities):
            if not first:
                yield ','
            else:
                first = False
            if since_property is not None:
                row["_updated"] = row[since_property]
            yield ujson.dumps(row)
    yield ']'


@app.route("/<path:path>", methods=["GET"])
def get(path):
    request_url = "{0}{1}".format(url, path)
    logger.info(f"Requested url: {request_url}")

    query_string = None
    key = None
    use_paging_override = use_paging
    if since_property is not None:
        use_paging_override = False
    since = None

    if request.query_string:
        query_string = request.query_string.decode("utf-8")
        logger.info(f"Requested querystring: {query_string}")

        if request.args.get("_key") is not None:
            key = request.args["_key"]
        if request.args.get("_paging") is not None:
            use_paging_override = request.args["_paging"].lower() == "true"
        if request.args.get("since") is not None:
            since = request.args["since"]

        query_string = ""
        for query_string_key in request.args:
            if query_string_key != "_key" and query_string_key != "_paging" and query_string_key != "since":
                if query_string != "":
                    query_string += "&"
                query_string += f"{query_string_key}={request.args[query_string_key]}"
        if since is not None:
            query_string += f"&{since_property}={since}"

        logger.info(f"Updated querystring: {query_string}")

    try:
        if use_paging_override:
            entities = data_access_layer.get_paged_entities(url, path, query_string, key)
        else:
            entities = data_access_layer.get_all_entities(url, path, query_string, key)
    except Exception as e:
        logger.warning("Exception occurred when download data from '%s': '%s'", request_url, e)
        raise

    return Response(stream_json(entities), mimetype='application/json')


if __name__ == '__main__':
    cherrypy.tree.graft(app, '/')

    # Set the configuration of the web server to production mode
    cherrypy.config.update({
        'environment': 'production',
        'engine.autoreload_on': False,
        'log.screen': True,
        'server.socket_port': 5002,
        'server.socket_host': '0.0.0.0'
    })

    # Start the CherryPy WSGI web server
    cherrypy.engine.start()
    cherrypy.engine.block()
