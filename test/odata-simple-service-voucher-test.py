#python3 -m unittest odata-simple-service-voucher-test.py

import unittest

import sys
import os
service_dir = os.path.abspath('..') + os.path.dirname('/service')
sys.path.append(service_dir)

from service import logger
from service import BasicUrlSystem
from service import VoucherDataAccess

import ujson
import datetime

headers_parameter =  os.environ.get("headers_parameter",'{"Content-Type":"application/json"}')

class TestStringMethods(unittest.TestCase):
    
    def test_env(self):
        url = os.environ.get("base_url","https://api-test.statnett.no/services/erp/projection/v1/GLVoucherRowsProjAnalysis/GenLedProjVoucherRowSet?$top=1&$count=true&$orderby=AccountingYear asc&$select=AccountingYear ")
        log = logger.Logger('odata-simple-test')
        log.info(f"base_url: {url}")

    def test_BasicUrlSystem(self):
        headers = ujson.loads('{"Content-Type":"application/json","Authorization":"Basic U1VUSE9NQVNESVQ6RXZlNGV2ZXIhIQ=="}')
        session_factory = BasicUrlSystem.BasicUrlSystem({"headers": headers})
        with session_factory.make_session() as s:
            request_data = s.request("GET", "https://api-test.statnett.no/services/erp/projection/v1/GLVoucherRowsProjAnalysis/GenLedProjVoucherRowSet?$top=1&$count=true&$orderby=AccountingYear asc&$select=AccountingYear ", headers=headers)
            log = logger.Logger('odata-simple-test')
            log.info(f"request_data: {request_data}")

    def test_DataAccess_createRequestString(self):
        dataaccess = VoucherDataAccess.DataAccess()
        requeststring = dataaccess.createRequestString("https://api-test.statnett.no/services/erp/projection/v1/GLVoucherRowsProjAnalysis/GenLedProjVoucherRowSet",2022, 2, 1000)
        log = logger.Logger('odata-simple-test')
        log.info(f"requeststring: {requeststring}")
        self.assertEqual("https://api-test.statnett.no/services/erp/projection/v1/GLVoucherRowsProjAnalysis/GenLedProjVoucherRowSet?$count=true&$top=1000&$skip=1000&$filter=AccountingYear%20eq%202022%20and%20AccountingPeriod%20eq%202%0A&$orderby=VoucherNo%20asc", requeststring)

    def test_getEntities(self):
        log = logger.Logger('odata-simple-test')      
        
        start = datetime.datetime.now()
        start_time = start.strftime("%H:%M:%S")
        
        dataaccess = VoucherDataAccess.DataAccess()
        endyear = datetime.date.today().year
        entities = dataaccess.getEntities(headers_parameter)
    
        for entity in entities:
            test = 1
            
        end = datetime.datetime.now()
        end_time = end.strftime("%H:%M:%S")
        
        time_span = end - start
        log.info(F"Start {start_time} End {end_time} Time spendt: {time_span}")
        
    def test_upper(self):
        self.assertEqual('FOO', 'FOO')

if __name__ == '__main__':
    unittest.main()