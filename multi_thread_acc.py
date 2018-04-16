"""
Simple example that connects to the first Crazyflie found, logs the Stabilizer
and prints it to the console. After 10s the application disconnects and exits.
"""
import logging
import time
from threading import Timer
from threading import Thread
from threading import Lock
import os.path
import numpy as np
from transforms3d.euler import quat2euler

import cflib.crtp  # noqa
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie

# Only output errors from the logging framework
from cflib.positioning.motion_commander import MotionCommander

# Only output errors from the logging framework
logging.basicConfig(level=logging.ERROR)


class LoggingExample:
    """
    Simple logging example class that logs the Stabilizer from a supplied
    link uri and disconnects after 5s.
    """

    def __init__(self, link_uri):
        """ Initialize and run the example with the specified link_uri """

        self._cf = Crazyflie(rw_cache='./cache')

        # Connect some callbacks from the Crazyflie API
        self._cf.connected.add_callback(self._connected)
        self._cf.disconnected.add_callback(self._disconnected)
        self._cf.connection_failed.add_callback(self._connection_failed)
        self._cf.connection_lost.add_callback(self._connection_lost)

        print('Connecting to %s' % link_uri)

        # Try to connect to the Crazyflie
        # Lock the connection part to speed up
        lock = Lock()
        lock.acquire()
        self._cf.open_link(link_uri)
        lock.release()


        # Variable used to keep main loop occupied until disconnect
        self.my_connected = False

    def _connected(self, link_uri):
        """ This callback is called form the Crazyflie API when a Crazyflie
        has been connected and the TOCs have been downloaded."""
        print('Connected to %s' % link_uri)
        self.my_connected = True

        # The definition of the logconfig can be made before connecting
        # self._lg_stab = LogConfig(name='Stabilizer', period_in_ms=10)
        # set acceleration log config
        self._lg_acc = LogConfig(name="acc", period_in_ms=10)
        self._lg_acc.add_variable('acc.x', 'float')
        self._lg_acc.add_variable('acc.y', 'float')
        self._lg_acc.add_variable('acc.z', 'float')

        # vec, theta = euler2axangle(0, 1.5, 9, 'szyx')

        # open file in log directory
        # save_path = './log'
        curr_time = time.strftime("%Y%m%d-%H%M%S")
        # file_name = os.path.join(save_path, 'acc_'+curr_time+'.txt')
        file_name = 'acc_' + curr_time + '.txt'

        self.f = open(file_name, 'w')
        # Adding the configuration cannot be done until a Crazyflie is
        # connected, since we need to check that the variables we
        # would like to log are in the TOC.
        try:
            self._cf.log.add_config(self._lg_acc)
            # This callback will receive the data
            self._lg_acc.data_received_cb.add_callback(self._stab_log_data)
            # This callback will be called on errors
            self._lg_acc.error_cb.add_callback(self._stab_log_error)
            # Start the logging
            self._lg_acc.start()
        except KeyError as e:
            print('Could not start log configuration,'
                  '{} not found in TOC'.format(str(e)))
        except AttributeError:
            print('Could not add Stabilizer log config, bad configuration.')

    def _stab_log_error(self, logconf, msg):
        """Callback from the log API when an error occurs"""
        print('Error when logging %s: %s' % (logconf.name, msg))

    def _stab_log_data(self, timestamp, data, logconf):
        """Callback froma the log API when data arrives"""
        self.f.write('[%d][%s]: %s' % (timestamp, logconf.name, data) + "\n")
        print('[%d][%s]: %s' % (timestamp, logconf.name, data))

    def _connection_failed(self, link_uri, msg):
        """Callback when connection initial connection fails (i.e no Crazyflie
        at the speficied address)"""
        print('Connection to %s failed: %s' % (link_uri, msg))
        self.my_connected = False
        # self.f.close()


    def _connection_lost(self, link_uri, msg):
        """Callback when disconnected after a connection has been made (i.e
        Crazyflie moves out of range)"""
        print('Connection to %s lost: %s' % (link_uri, msg))
        self.my_connected = False
        # self.f.close()


    def _disconnected(self, link_uri):
        """Callback when the Crazyflie is disconnected (called in all cases)"""
        print('Disconnected from %s' % link_uri)
        self.my_connected = False
        self.f.close()

    def disconnect(self):
        """Disconnect everything and stop logging when called"""
        print('Disconnect in 1 second')

        t = Timer(1, self._cf.close_link)
        t.start()


def motion1(le_uri):

    le = LoggingExample(le_uri)

    while not le.my_connected:
        pass

    with MotionCommander(le._cf) as mc:
        # Test Actions
        # mc.take_off()
        print('Taking off!')
        time.sleep(1)

        # print('Moving up 0.01m')
        mc.forward(0.2)
        mc.down(0.3)
        le.disconnect()


def motion2(le_uri):
    le = LoggingExample(le_uri)

    while not le.my_connected:
        pass

    with MotionCommander(le._cf) as mc:
        # Test Actions
        # mc.take_off()
        print('Taking off!')
        time.sleep(1)

        # print('Moving up 0.01m')
        mc.up(0.2)
        mc.down(0.5)
        le.disconnect()


if __name__ == '__main__':
    # Initialize the low-level drivers (don't list the debug drivers)
    cflib.crtp.init_drivers(enable_debug_driver=False)
    # Scan for Crazyflies and use the first one found
    print('Scanning interfaces for Crazyflies...')
    available = cflib.crtp.scan_interfaces()

    print('Crazyflies found:')
    for i in available:
        print(i[0])

    if len(available) <= 0:
        print('No Crazyflies found, cannot run example')
    else:
        t1 = Thread(target=motion1, args=(available[0][0], ))
        t2 = Thread(target=motion2, args=(available[1][0], ))

        t1.start()
        t2.start()



