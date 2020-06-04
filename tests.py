import automation
import logging, odoorpc, time, argparse

#setup logger
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
_logger = logging.getLogger("Test Machine")

class TestMachine(automation.MRP_Automation):

    def __init__(self, api, asset_id):
        _logger.info("Machine INIT Compleete.")

        #init super classes
        super(TestMachine, self).__init__(api, asset_id)

        #pass the route lanes into the machine for the node_queue to assign.
        self.route_lanes = [MRP_Carrier_Lane_0(self.api, self), MRP_Carrier_Lane_1(self.api, self)]
        pass

class MRP_Carrier_Lane_0(automation.MRP_Carrier_Lane):
    def __init__(self, api, mrp_automation_machine):
        super(MRP_Carrier_Lane_0, self).__init__(api, mrp_automation_machine)
        self._logger = logging.getLogger("Carrier Lane 0")

    def preflight_checks(self):
        time.sleep(5)
        return True

    def ingress_trigger(self):
        if len(self.route_node_carrier_queue) > 0:
            return True
        return False

    def process_ingress(self):
        time.sleep(5)
        return True

    def process_egress(self):
        time.sleep(5)
        return True

class MRP_Carrier_Lane_1(automation.MRP_Carrier_Lane):
    def __init__(self, api, mrp_automation_machine):
        super(MRP_Carrier_Lane_1, self).__init__(api, mrp_automation_machine)
        self._logger = logging.getLogger("Carrier Lane 1")
        pass

    def preflight_checks(self):
        time.sleep(5)
        return True

    def ingress_trigger(self):
        if len(self.route_node_carrier_queue) > 0:
            return True
        return False

    def process_ingress(self):
        time.sleep(5)
        return True

    def process_egress(self):
        time.sleep(5)
        return True

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
    test_machine.button_start()
    while True:
        time.sleep(1000)