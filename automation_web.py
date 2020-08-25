from flask import Flask, render_template
import json

app = Flask(__name__)

class Automation_Webservice(object):
    def start_webservice(self):
        app.add_url_rule('/', 'home', view_func=self.index)
        app.add_url_rule('/machine_vars/', 'machine vars', view_func=self.machine_vars)
        app.add_url_rule('/carrier_queue/<lane_index>', 'carrier queue', view_func=self.carrier_queue)

        app.run(debug=True, host='0.0.0.0', port=int("5000"))
        pass

    def index(self):
        return render_template('index.html', machine=self)
        
    def machine_vars(self):
        var={}
        var['run_status'] = self.run_status
        var['e_stop_status'] = self.e_stop_status
        var['busy'] = self.busy
        var['warn'] = self.warn
        return json.dumps(var)
        
    def carrier_queue(self, lane_index):
        return render_template("carrier_lane_queue.html", carrier_lane=self.route_lanes[int(lane_index)] )