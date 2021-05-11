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
page_size = os.environ.get("page_size", 1000)
use_count = os.environ.get("use_count_for_paging", "false").lower() == "true"
headers = ujson.loads('{"Content-Type": "application/json"}')


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

    def __get_all_paged_entities(self, base_url, path, query_string):
        logger.info(f"Fetching data from paged url: {path}")
        request_url = "{0}{1}".format(base_url, path)
        use_count_parameter = ""
        if use_count:
            use_count_parameter = "&$count=true"

        if query_string:
            next_page = "{0}?{1}&$top={2}{3}".format(request_url, query_string.decode("utf-8"), page_size, use_count_parameter)
        else:
            next_page = "{0}?$top={1}{2}".format(request_url, page_size, use_count_parameter)

        entity_count = 0
        page_count = 0
        count = None
        previous_page = None
        while next_page is not None and next_page != previous_page:
            logger.info(f"Fetching data from url: {next_page}")

            with session_factory.make_session() as s:
                request_data = s.request("GET", next_page, headers=headers)

            if not request_data.ok:
                error_text = f"Unexpected response status code: {request_data.status_code} with response text {request_data.text}"
                logger.error(error_text)
                raise AssertionError(error_text)

            result_json = Dotdictify(request_data.json())
            entities = result_json.get(value_field)
            for entity in entities:
                if entity is not None:
                    yield (entity)

            entity_count += len(entities)
            if count is None and use_count:
                count = result_json["@odata.count"]
                logger.info(f"Total number of entities in source: {count}")
            page_count += 1

            logger.info(f"Fetched {len(entities)} entities, total: {entity_count}")

            previous_page = next_page

            if len(entities) == 0:
                next_page = None
            else:
                next_page = get_next_url(request_url, count, entity_count, query_string)

        logger.info(f"Returning {entity_count} entities from {page_count} pages")

    def get_paged_entities(self, base_url, path, query_string):
        return self.__get_all_paged_entities(base_url, path, query_string)


data_access_layer = DataAccess()


def get_next_url(base_url, count, entities_fetched, query_string):
    if use_count and entities_fetched >= count:
        return None

    if query_string:
        request_url = "{0}?{1}&$top={2}&$skip={3}".format(base_url, query_string.decode("utf-8"), page_size, entities_fetched)
    else:
        request_url = "{0}?$top={1}&$skip={2}".format(base_url, page_size, entities_fetched)

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
    if request.query_string:
        request_url = "{0}?{1}".format(request_url, request.query_string.decode("utf-8"))

    logger.info("Requested url: %s", request_url)

    try:
        entities = data_access_layer.get_paged_entities(url, path, request.query_string)
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
