import automation
import logging, odoorpc, threading, time, argparse

#setup logger
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG)
_logger = logging.getLogger("Test Machine")

class TestMachine(automation.Machine):

    def __init__(self, api, asset_id):
        _logger.info("Machine INIT Compleete.")
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

    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--equipment-id', type=int, help='ODOO Maintence Equipment ID')
    args = parser.parse_args()

    #create instance of this test machine, and start its engine
    test_machine = TestMachine(api=odoo, asset_id=args.equipment_id)
    test_machine.button_start(
                              )
    while True:
        time.sleep(1000)