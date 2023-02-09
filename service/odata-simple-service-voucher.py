#python3 odata-simple-service-voucher.py

#curl -o output.json -N -v -H "Content-Type: application/json" -H "Connection: Keep-Alive" -H "accept-encoding: gzip, deflate" -H "Expect: 100-continue" http://127.0.0.2:8080/ -u "SUTHOMASDIT:<pass>"

#for browser
#export headers_parameter='{"Content-Type":"application/json","Authorization":"Basic U1VUSE9NQVNESVQ6RXZlNGV2ZXIhIQ=="}'

import logger
import os
import cherrypy
import ujson
from flask import Flask, Response, request
import datetime
import VoucherDataAccess

app = Flask(__name__)
logger = logger.Logger('odata-simple')

get_StartYear = os.environ.get("get_StartYear", 2021)
get_EndYear = os.environ.get("get_EndYear",datetime.date.today().year)
get_StartAccountPeriode = int(os.environ.get("get_StartAccountPeriode", 1))
get_EndAccountPeriode = os.environ.get("get_EndAccountPeriode", 12)

def stream_json(entities):
    first = True
    yield '['
    if entities is not None:
        for i, row in enumerate(entities):
            if not first:
                yield ','
            else:
                first = False
            yield ujson.dumps(row)
    yield ']'

@app.route("/", methods=["GET"])
def get():
    dataaccess = VoucherDataAccess.DataAccess()
    try:
        entities = dataaccess.getEntities(cherrypy.request.headers, get_StartYear, get_EndYear, get_StartAccountPeriode, get_EndAccountPeriode)
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
        'server.socket_port': 8080,
        'server.socket_host': '0.0.0.0'
    })

    # Start the CherryPy WSGI web server
    cherrypy.engine.start()
    cherrypy.engine.block()