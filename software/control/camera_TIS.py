import numpy
import gi
from collections import namedtuple
from time import sleep
import sys
import time #@@@

gi.require_version("Gst", "1.0")
gi.require_version("Tcam", "0.1")

from gi.repository import Tcam, Gst, GLib, GObject

DeviceInfo = namedtuple("DeviceInfo", "status name identifier connection_type")
CameraProperty = namedtuple("CameraProperty", "status value min max default step type flags category group")


class TISCamera(object):

    def __init__(self,serial, width, height, framerate, color):
        Gst.init(sys.argv)
        self.height = height
        self.width = width
        self.sample = None
        self.samplelocked = False
        self.newsample = False
        self.gotimage = False
        self.img_mat = None
        self.new_image_callback_external = None
        self.image_locked = False

        format = "BGRx"
        if(color == False):
            format="GRAY8"

        if(framerate == 2500000):    
            p = 'tcambin serial="%s" name=source ! video/x-raw,format=%s,width=%d,height=%d,framerate=%d/10593' % (serial,format,width,height,framerate,)
        else:
            p = 'tcambin serial="%s" name=source ! video/x-raw,format=%s,width=%d,height=%d,framerate=%d/1' % (serial,format,width,height,framerate,)

        p += ' ! videoconvert ! appsink name=sink'

        print(p)
        try:
            self.pipeline = Gst.parse_launch(p)
        except GLib.Error as error:
            print("Error creating pipeline: {0}".format(err))
            raise

        self.pipeline.set_state(Gst.State.READY)
        self.pipeline.get_state(Gst.CLOCK_TIME_NONE)
        # Query a pointer to our source, so we can set properties.
        self.source = self.pipeline.get_by_name("source")

        # Query a pointer to the appsink, so we can assign the callback function.
        self.appsink = self.pipeline.get_by_name("sink")
        self.appsink.set_property("max-buffers",5)
        self.appsink.set_property("drop", True)
        self.appsink.set_property("emit-signals", True)

    def open(self,index=0):
        pass

    def set_callback(self,function):
        self.new_image_callback_external = function

    def enable_callback(self):
        self.appsink.connect('new-sample', self._on_new_buffer)

    def disable_callback(self):
        pass

    def open_by_sn(self,sn):
        pass

    def close(self):
        pass

    def set_exposure_time(self,exposure_time):
        self._set_property('Exposure Auto',False)
        self._set_property('Exposure',exposure_time)

    def set_analog_gain(self,analog_gain):
        self._set_property('Gain Auto',False)
        self._set_property('Gain',analog_gain)

    def get_awb_ratios(self):
        pass

    def set_wb_ratios(self, wb_r=None, wb_g=None, wb_b=None):
        pass

    def start_streaming(self):
        try:
            self.pipeline.set_state(Gst.State.PLAYING)
            self.pipeline.get_state(Gst.CLOCK_TIME_NONE)

        except GLib.Error as error:
            print("Error starting pipeline: {0}".format(err))#error?
            raise
        self.frame_ID = 0

    def stop_streaming(self):
        self.pipeline.set_state(Gst.State.NULL)
        print("pipeline stopped")
        self.pipeline.set_state(Gst.State.READY)

    def set_continuous_acquisition(self):
        self._set_property('Trigger Mode', False)

    def set_software_triggered_acquisition(self):
        pass

    def set_hardware_triggered_acquisition(self):
        self._set_property('Trigger Mode', True)
        self._set_property('Trigger Polarity', 'RisingEdge')
        self._set_property('Trigger Delay (us)', 0)

    def send_trigger(self):
        pass

    def read_frame(self):
        return self.current_frame

    def _on_new_buffer(self, appsink):
        # Function that is called when a new sample from camera is available
        self.newsample = True
        # print('new buffer received: ' + str(time.time())) #@@@
        if self.image_locked:
            print('last image is still being processed, a frame is dropped')
            return
        if self.samplelocked is False:
            self.samplelocked = True
            try:
                self.sample = self.appsink.get_property('last-sample')
                self._gstbuffer_to_opencv()
                # print('new buffer read into RAM: ' + str(time.time())) #@@@
                self.samplelocked = False
                self.newsample = False
                # gotimage reflects if a new image was triggered
                self.gotimage = True
                self.frame_ID = self.frame_ID + 1 # @@@ read frame ID from the camera
                self.timestamp = time.time()
                if self.new_image_callback_external is not None:
                    self.new_image_callback_external(self)
            except GLib.Error as error:
                print("Error on_new_buffer pipeline: {0}".format(err)) #error
                self.img_mat = None
        return Gst.FlowReturn.OK

    def _get_property(self, PropertyName):
        try:
            return CameraProperty(*self.source.get_tcam_property(PropertyName))
        except GLib.Error as error:
            print("Error get Property {0}: {1}",PropertyName, format(err))
            raise

    def _set_property(self, PropertyName, value):
        try:
            self.source.set_tcam_property(PropertyName,GObject.Value(type(value),value))
        except GLib.Error as error:
            print("Error set Property {0}: {1}",PropertyName, format(err))
            raise

    def _gstbuffer_to_opencv(self):
        # Sample code from https://gist.github.com/cbenhagen/76b24573fa63e7492fb6#file-gst-appsink-opencv-py-L34
        buf = self.sample.get_buffer()
        caps = self.sample.get_caps()
        bpp = 4;
        if caps.get_structure(0).get_value('format') == "BGRx":
            bpp = 4;

        if caps.get_structure(0).get_value('format') == "GRAY8":
            bpp = 1;

        self.current_frame = numpy.ndarray(
            (caps.get_structure(0).get_value('height'),
             caps.get_structure(0).get_value('width'),
             bpp),
            buffer=buf.extract_dup(0, buf.get_size()),
            dtype=numpy.uint8)