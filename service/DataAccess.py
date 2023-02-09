from service import logger
from service import BasicUrlSystem
import os
import ujson
import datetime

page_url = os.environ.get("base_url", "https://api-test.statnett.no/services/erp/projection/v1")
page_path = os.environ.get("page_path", "/GLVoucherRowsProjAnalysis/GenLedProjVoucherRowSet")
page_size = int(os.environ.get("page_size", 1000))
page_size_parameter = os.environ.get("page_size_parameter")
page_parameter = os.environ.get("page_parameter")
headers_parameter =  os.environ.get("headers_parameter",'{"Content-Type":"application/json"}')
key = os.environ.get("key","value") 


class DataAccess:

    def __init__(self):
        self.logger = logger.Logger('odata-simple-DataAccess')

    def getEntities(self, startyear = 2021, endyear = datetime.date.today().year, startmonth = 1, endmonth = 12):
      
        if(startyear>endyear):
            raise
            
        if(startmonth>endmonth):
            raise
        
        if(startmonth<1):
            raise
        
        if(startmonth>12):
            raise
        
        if(endmonth<1):
            raise
        
        if(endmonth>12):
            raise
      
        request_url = "{0}{1}".format(page_url, page_path)
        
        headers = ujson.loads(headers_parameter)
        session_factory = BasicUrlSystem.BasicUrlSystem({"headers": headers})
      
        entity_count = 0
      
        for year in range(startyear, endyear+1,1):
            for month in range(startmonth,endmonth+1,1):
                requeststring = self.createRequestString(request_url,year,month,0)
                previousrequeststring = ""
                count = 0
                while requeststring is not None and requeststring != previousrequeststring:
                    with session_factory.make_session() as s:
 
                        request_data = s.request("GET", requeststring, headers=headers)
                        
                        if not request_data.ok:
                            error_text = f"Unexpected response status code: {request_data.status_code} with response text " \
                                f"{request_data.text}"
                            self.logger.error(error_text)
                            raise AssertionError(error_text)

                        entities = request_data.json()[key]
                        entities_count = request_data.json()["@odata.count"]
                        
                        if entities is not None:
                            for entity in entities:
                                if entity is not None:
                                    yield (entity)
                        else:
                            entities = []

                        count += len(entities)
                        self.logger.info(f"Year:{year} month:{month} entities: {entities_count}/{count} bytes {len(request_data.content)}")

                        if len(entities) == 0 or len(entities) < page_size or count >= entities_count:
                            requeststring = None
                        else:
                            previousrequeststring = requeststring
                            requeststring = self.createRequestString(request_url, year,month, count)
    
                entity_count += count
    
        self.logger.info(f"Returning {entity_count} entities")
            
    def createRequestString(self, request_url,page_accountingyear, page_accountingperiod, page_skip):
        requeststringformat="{0}?$count=true&$top={1}&$skip={2}&$filter=AccountingYear%20eq%20{3}%20and%20AccountingPeriod%20eq%20{4}%0A&$orderby=VoucherNo%20asc"
        requeststring = requeststringformat.format(request_url, page_size, page_skip, page_accountingyear, page_accountingperiod)
        return requeststring
        
       