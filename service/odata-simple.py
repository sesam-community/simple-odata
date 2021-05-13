import ujson
import requests
from flask import Flask, Response, request
import os
import logger
import cherrypy
from sesamutils import Dotdictify


app = Flask(__name__)
logger = logger.Logger('odata-simple')

url = os.environ.get("base_url")
value_field = os.environ.get("value_field", "value")
page_size = int(os.environ.get("page_size", 1000))
page_size_parameter = os.environ.get("page_size_parameter")
page_parameter = os.environ.get("page_parameter")
use_page_as_counter = os.environ.get("use_page_as_counter", "false") == "true"
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

    def get_value_field(d, event):
        for key in d.keys():
            if re.match(key, event):
                yield d[key]

    def __get_all_paged_entities(self, base_url, path, query_string, key):
        logger.info(f"Fetching data from paged url: {path}")
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

            result_json = Dotdictify(request_data.json())
            entities = result_json.get(key)
            for entity in entities:
                if entity is not None:
                    yield (entity)

            entity_count += len(entities)
            page_count += 1

            logger.info(f"Fetched {len(entities)} entities, total: {entity_count}")

            previous_page = next_page

            if len(entities) == 0:
                next_page = None
            else:
                next_page = get_next_url(request_url, entity_count, query_string, page_count)

        logger.info(f"Returning {entity_count} entities from {page_count} pages")

    def get_paged_entities(self, base_url, path, query_string, key):
        return self.__get_all_paged_entities(base_url, path, query_string, key)


data_access_layer = DataAccess()


def get_next_url(base_url, entity_count, query_string, page_count):
    next_count = entity_count
    if use_page_as_counter:
            next_count = page_count

    if query_string:
        request_url = "{0}?{1}&{2}={3}&4}={5}".format(base_url, query_string, page_size_parameter,
                                                      page_size, page_parameter, next_count)
    else:
        request_url = "{0}?{1}={2}&{3}={4}".format(base_url, page_size_parameter, page_size,
                                                   page_parameter, next_count)

    return request_url


def call_url(base_url, url_parameters, page):
    request_url = base_url
    first = True
    for k, v in url_parameters.items():
        if first:
            if k == os.environ.get('startpage'):
                request_url += '?' + k + '=' + page
            else:
                request_url += '?' + k + '=' + v
        else:
            if k == os.environ.get('startpage'):
                request_url += '&' + k + '=' + page
            else:
                request_url += '&' + k + '=' + v
        first = False
    return request_url


def stream_json(entities):
    first = True
    yield '['
    for i, row in enumerate(entities):
        if not first:
            yield ','
        else:
            first = False
        yield ujson.dumps(row)
    yield ']'


@app.route("/<path:path>", methods=["GET"])
def get(path):
    request_url = "{0}{1}".format(url, path)
    query_string = None
    key = None
    if request.query_string:
        query_string = request.query_string.decode("utf-8")
        request_url = "{0}?{1}".format(request_url, query_string)
        if request.args.get("_key") is not None:
            key = request.args["_key"]
            query_string = ""
            for query_string_key in request.args:
                if query_string_key != "_key":
                    if query_string != "":
                        query_string += "&"
                    query_string += f"{query_string_key}={request.args[query_string_key]}"

    logger.info("Requested url: %s", request_url)

    try:
        entities = data_access_layer.get_paged_entities(url, path, query_string, key)
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
