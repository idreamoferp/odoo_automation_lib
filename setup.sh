#update apt repos
sudo apt update && sudo apt upgrade

#install pip items
sudo pip3 install Adafruit-BBIO Adafruit-Blinka odoorpc numpy

#download and run install helpers
git clone http://github.com/idreamoferp/install_helpers
cd install_helpers

#install OpenCV for Python 3.7
git chekcout opencv_python_3
bash install_opencv_python_3-7-3

#install FreeNECT for Python 3
git checkout kinect_python3
bash install_kinect.sh