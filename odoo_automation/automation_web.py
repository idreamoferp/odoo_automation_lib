from flask import Flask, render_template, request
import json, threading, os

class Automation_Webservice(object):
    def __init__(self, api, asset_id):
        pass
    
    def start_webservice(self):
        template_dir = os.path.dirname(__file__) + '/templates'
        self.flask = app = Flask("MRP_Automation", template_folder=template_dir)
        
        #setup routes
        self.flask.add_url_rule('/', 'home', view_func=self.index)
        self.flask.add_url_rule('/workcenters_drop/', 'workcenters_drop', view_func=self.get_workcenters_drop)
        self.flask.add_url_rule('/workorders_list/', 'workorders', view_func=self.get_workorders)
        self.flask.add_url_rule('/workorder/<workorderID>', 'workorder detail', methods=['GET', 'POST'], view_func=self.get_workorder)
        self.flask.add_url_rule('/machine_vars/', 'machine vars', view_func=self.machine_vars)
        self.flask.add_url_rule('/carrier_queue/<lane_index>', 'carrier queue', view_func=self.carrier_queue)
        
        self.flask_thread = threading.Thread(target=self._start_server, daemon=True)
        self.flask_thread.start()
        pass
    
    def _start_server(self):
        
        self.flask.run(host=self.config['webservice']['ip_address'], port=int(self.config['webservice']['port']), threaded=True)
        
    def index(self):
        return render_template('index.html', machine=self)
    
    def get_workcenters_drop(self):
        domain = []
        api_workcenters = self.api.env['mrp.workcenter']
        workcenter_ids = api_workcenters.browse(api_workcenters.search(domain))
        
        workcenter_ids_checked = [int(i) for i in self.config['mrp']['workcenter_ids'].split(",")] 
        
        return render_template('workcenters_drop.html', workcenter_ids=workcenter_ids, workcenter_ids_checked=workcenter_ids_checked)
    
    def get_workorders(self):
        #read workcenters in config file, convert string to list of ints
        workcenter_ids =  [int(i) for i in self.config['mrp']['workcenter_ids'].split(",")] 
        
        #build a search domain for odoo database
        domain = [('workcenter_id', 'in', workcenter_ids), ('state', 'in', ['progress', 'ready'])]
        
        #return a recordset of work orders to pass into template rendering from odoo database
        workorder_ids = False
        try:
            workorder_ids = self.api.env['mrp.workorder'].search(domain)
            workorder_ids = self.api.env['mrp.workorder'].browse(workorder_ids)
        except Exception as e:
            logger.warn("could not get traveler list /r/n/ %s " % (e))
        
        return render_template('workorder_list.html', workorder_ids=workorder_ids)
        
    def get_workorder(self, workorderID):
        
        cmd = False
        if "cmd" in request.args:
            cmd=request.args.get("cmd")
        if "cmd" in request.form:
            cmd=request.form.get("cmd")
        
        api_workorder = self.api.env['mrp.workorder']
        workorder_id = False
        try:
            workorder_id = api_workorder.browse(int(workorderID))
        except Exception as e:
            logger.warn("could not get traveler list /r/n/ %s " % (e))
        
        if cmd =="start_working":
            if not workorder_id.is_user_working:
                workorder_id.button_start()
        
        if cmd =="stop_working":
            workorder_id.button_pending()
        
        workorder_id = api_workorder.browse(int(workorderID))
        
        return render_template('workorder_detail.html', workorder_id=workorder_id, machine=self)
        
    def machine_vars(self):
        var={}
        var['run_status'] = self.run_status
        var['e_stop_status'] = self.e_stop_status
        var['busy'] = self.busy
        var['warn'] = self.warn
        return json.dumps(var)
        
    def carrier_queue(self, lane_index):
        return render_template("carrier_lane_queue.html", carrier_lane=self.route_lanes[int(lane_index)] )
        
        