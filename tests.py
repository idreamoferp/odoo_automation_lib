import automation, json
import logging, odoorpc, time, argparse
from flask import Flask, render_template

#setup logger
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
_logger = logging.getLogger("Test Machine")

#setup flask
app = Flask(__name__)

test_machine = False

@app.route("/")
def index():
   
    return render_template('index.html', machine=test_machine)
        
@app.route("/machine_vars")
def machine_vars():
    var={}
    var['run_status'] = test_machine.run_status
    var['e_stop_status'] = test_machine.e_stop_status
    var['busy'] = test_machine.busy
    var['warn'] = test_machine.warn
    return json.dumps(var)
    
@app.route("/route_node")
def route_node():
    var={}
    var['route_lanes'] = test_machine.route_lanes
    var['route_node_id'] = {}
    if test_machine.route_node_id:
        var['route_node_id']['id'] = test_machine.route_node_id.id
        var['route_node_id']['name'] = test_machine.route_node_id.name
        
    return json.dumps(var)
    
class TestMachine(automation.MRP_Automation):

    def __init__(self, api, asset_id):
        _logger.info("Machine INIT Compleete.")

        #init super classes
        super(TestMachine, self).__init__(api, asset_id)
        
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
    
    #press start button (for headless operation)
    test_machine.button_start()
    
    app.run(debug=True, host='0.0.0.0', port=int("5000"))
    
        
    while True:
        time.sleep(1000)