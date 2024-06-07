# update your system
sudo apt update
sudo apt upgrade

# make sure to activate your mamba environment for this project

mamba activate squid-station

# install packages
mamba install anaconda::pip
pip3 install pyqtgraph
pip3 install PyQt5

# clone the repo
sudo apt-get install git -y
cd ~/Desktop
git clone https://github.com/wenzel-lab/SQUID-bioimaging-platform.git
cd SQUID-bioimaging-platform/software
mkdir cache

# install libraries 
pip3 install qtpy pyserial pandas imageio crc==1.3.0 lxml numpy tifffile scipy
pip3 install opencv-python-headless opencv-contrib-python-headless

# install camera drivers
cd ~/Desktop/SQUID-bioimaging-platform/software/drivers\ and\ libraries/daheng\ camera/Galaxy_Linux-x86_Gige-U3_32bits-64bits_1.2.1911.9122
./Galaxy_camera.run
cd ~/Desktop/SQUID-bioimaging-platform/software/drivers\ and\ libraries/daheng\ camera/Galaxy_Linux_Python_1.0.1905.9081/api
python3 setup.py build

# depending on how you link your system, sudo python3 may not be called properly, add a path to your python3 executable from your environment if needed
sudo /home/wenzel-lab/miniforge3/envs/squid-station/bin/python3 setup.py install

# enable access to serial ports without sudo
sudo usermod -aG dialout $USER

# to use main.py
pip3 install napari

# place the .ini file in the software folder for proper execution of the software
cp cd ~/Desktop/SQUID-bioimaging-platform/software/configurations/configuration_squid_6060.ini ../
