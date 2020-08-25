import threading
import time

#setup logger
import logging
_logger = logging.getLogger("Kinect Subsytem")

class Kinect():
	def __init__(self, device_index=0):
		self.device_index = device_index
		self.device_version = False
		self.lib_freenect = False
		#frame buffers
		self.depth_lock = threading.Lock()
		self.depth_frame_buffer = None
		self.depth_timestamp = None
		
		self.video_lock = threading.Lock()
		self.video_frame_buffer = None
		self.video_timestamp = None
		
		self.run_loop_thread = threading.Thread(target=self.run_loop)
		
		pass
	
	def detect_freenect_ver(self, device_index=0):
		import freenect
		self.lib_freenect = freenect
		pass
		
	def _depth_cb(self, dev, data, timestamp):
		with self.depth_lock:
			self.depth_frame_buffer = data.copy()
			self.depth_timestamp = timestamp
		pass
	
	def _video_cb(self, dev, data, timestamp):
		with self.video_lock:
			self.video_frame_buffer = data.copy()
			self.video_timestamp = timestamp
		pass
	
	def _body_cb(self, dev, data, timestamp):
		pass
	
	def run_loop(self):
		while 1:
			if self.lib_freenect:
				try:
					self.lib_freenect.runloop(depth=self._depth_cb, video=self._video_cb, body=self._body_cb)
				except Exception as e:
					pass
				
				
class KinectWebService():
	from flask import Response
	from flask import Flask
	from flask import render_template
	import cv2
	
	#global vars
	app = Flask(__name__) #flask application to attache routes
	
	def __init__(self, flask_app=None, device_index=0):
		#global app, devices
		if flask_app:
			app = flask_app
		
		self.device = Kinect(device_index)
		self.device.video_feed_modifiers = lambda buf : buf
		self.device.depth_feed_modifiers = lambda buf : buf
		pass
	
	def generate_video():
		
		# loop over frames from the output stream
		while True:
			# wait until the lock is acquired
			with self.device.video_lock:
				#copy frame buffer to outputFrame
				outputFrame = self.device.video_frame_buffer.copy()
				
				# check if the output frame is available, otherwise skip the iteration of the loop
				if outputFrame is None:
					continue
				
				#apply external modifiers to feed
				outputFrame = self.device.video_feed_modifiers(outputFrame)
					
				# encode the frame in JPEG format
				(flag, encodedImage) = cv2.imencode(".jpg", outputFrame)
	
				# ensure the frame was successfully encoded
				if not flag:
					continue
	
			# yield the output frame in the byte format
			yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + bytearray(encodedImage) + b'\r\n')
	
	
	
	
	@app.route("/kinect/video_feed")
	def video_feed():
		# return the response generated along with the specific media type (mime type)
		return Response(generate_video(), mimetype = "multipart/x-mixed-replace; boundary=frame")


if __name__ == "__main__":
	from flask import Flask
	test_app = Flask(__name__)
	kinect = KinectWebService(flask_app=test_app)
	
	
	test_app.run(debug=True, host='0.0.0.0', port=int("5000"))