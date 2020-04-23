import automation
import logging, odoorpc, threading, time

#setup logger
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG)
_logger = logging.getLogger("Test Machine")

class TestMachine(automation.Machine):
    
    def __init__(self,api,asset_id):
        return super(TestMachine, self).__init__(api, asset_id)

#startup this machine
if __name__ == "__main__":
    
    #odoo api settings, TODO: move these to a server_config file
    server = "esg-beta.idreamoferp.com"
    port = 8012
    database = "ESG_Beta_1-0"
    user_id = "justin.mangini@esg.global"
    password = "ESGmaint0719"
    
    #create instance of odooRPC clinet with these settings
    odoo = odoorpc.ODOO(server, port=port)
    
    #attempt a login to odoo server to init the api
    try:
        odoo.login(database, user_id, password)
    except Exception as e:
        _logger.error("Error logging in to odoo server",e)
    
    #asset id from odoo's maintenance.equipment model space
    odoo_equipment_asset_id = 11519
    
    #create instance of this test machine, and start its engine
    test_machine = TestMachine(api=odoo, asset_id=odoo_equipment_asset_id)
    
    while True:
        time.sleep(1000)