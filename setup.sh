#update apt repos
sudo apt update && sudo apt upgrade

#install pip items
sudo pip3 install Adafruit-BBIO Adafruit-Blinka odoorpc numpy

#download and run install helpers
git clone http://github.com/idreamoferp/install_helpers
cd install_helpers
#install c9 helpers
git checkout cloud9
bash install_helpers.sh

#install OpenCV for Python 3.7
git checkout opencv_python_3
bash install_opencv_python_3-7-3

#install FreeNECT for Python 3
git checkout kinect_python3
bash install_kinect.sh