import logging, time, odoorpc, threading

class OdooDocuments():
    def __init__(self, odoo_api):
        self._odoo_api = odoo_api
        self._logger = logging.getLogger("ODOO Documents")
        self.cache_dir = "cache/filestore"
        self.document_page = self._odoo_api.env['document.page']
        
    def get_document_by_name(self, doc_name):
        domain = [("name","=",str(doc_name))]
        document_id = self.document_page.search(domain)
        document_id = self.document_page.browse(document_id)
        return document_id