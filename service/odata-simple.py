import json
import requests
from flask import Flask, Response
import os
import logger
import cherrypy

app = Flask(__name__)
logger = logger.Logger('odata-simple')

url = os.environ.get("base_url")
value_field = os.environ.get("value_field", "value")
log_response_data = os.environ.get("log_response_data", "false").lower() == "true"
stream_data = os.environ.get("stream_data", "true").lower() == "true"


def stream_odata_json(odata):
    """fetch entities from given Odata url and dumps back to client as JSON stream"""
    first = True
    yield '['
    data = json.loads(odata)

    for value in data[value_field]:
        if not first:
            yield ','
        else:
            first = False

        yield json.dumps(value)

    yield ']'


@app.route("/<path:path>", methods=["GET"])
def get(path):
    request_url = "{0}{1}".format(url, path)

    logger.info("Request url: %s", request_url)

    try:
        request_data = requests.get(request_url)
        if log_response_data:
            logger.info("Data received: %s", request_data.text)
    except Exception as e:
        logger.warning("Exception occurred when download data from '%s': '%s'", request_url, e)
        raise

    if stream_data:
        return Response(stream_odata_json(request_data.text), mimetype='application/json')

    return Response(request_data, mimetype='application/json')


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
