# Support for DS18B20 temperature sensors connected to the host
# (Linux 1-wire kernel driver, e.g. dtoverlay=w1-gpio,gpiopin=22)
#
# This module registers the "DS18B20_HOST" sensor type which reads the
# temperature from the w1 sysfs interface instead of from a Klipper MCU.
#
# NOTE: reading /sys/bus/w1/devices/<id>/w1_slave blocks until the sensor
# temperature conversion completes (~750ms). The read is therefore done in
# a background thread so the klippy reactor event loop is never blocked
# (a blocked reactor starves the MCU and triggers "Timer too close"
# shutdowns while homing/probing).
#
# Filtering: readings with a CRC error or exactly 85.000C (the DS18B20
# power-on reset value, returned when a conversion did not complete) are
# discarded and the last valid value is kept. Read errors never shut down
# the printer.
import logging
import threading
import time

DS18_REPORT_TIME = 3.0
POWERON_RAW = 85000

class DS18B20:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.name = config.get_name().split()[-1]
        self.reactor = self.printer.get_reactor()
        self.report_time = config.getfloat(
            'ds18_report_time', DS18_REPORT_TIME, minval=1.0)
        self.serial_no = config.get('serial_no')
        self.path = "/sys/bus/w1/devices/%s/w1_slave" % (self.serial_no,)
        self.temp = self.min_temp = self.max_temp = 0.0
        self._valid = True
        self._callback = None
        self._lock = threading.Lock()
        self._stop = False
        self._thread = threading.Thread(target=self._reader, daemon=True)
        self._thread.start()
        self._sample_timer = self.reactor.register_timer(self._sample_temp)
        self.printer.register_event_handler("klippy:connect",
                                            self.handle_connect)
        logging.info("ds18b20_sysfs: reading from %s" % (self.path,))
    def _read_raw(self):
        with open(self.path, 'r') as f:
            lines = f.readlines()
        if not lines[0].strip().endswith('YES'):
            return None, "crc error"
        raw = int(lines[1].split('t=')[1])
        if raw == POWERON_RAW:
            return None, "power-on value 85C"
        return raw, None
    def _set_valid(self, valid, reason=None):
        if valid == self._valid:
            return
        self._valid = valid
        if valid:
            logging.info("ds18b20_sysfs: %s readings recovered", self.name)
        else:
            logging.info("ds18b20_sysfs: %s discarding readings (%s),"
                         " holding last value", self.name, reason)
    def _reader(self):
        while not self._stop:
            try:
                raw, reason = self._read_raw()
            except Exception as e:
                raw, reason = None, "read error: %s" % (e,)
            if raw is None:
                self._set_valid(False, reason)
            else:
                self._set_valid(True)
                with self._lock:
                    self.temp = raw / 1000.0
            time.sleep(self.report_time)
    def handle_connect(self):
        self.reactor.update_timer(self._sample_timer, self.reactor.NOW)
    def setup_minmax(self, min_temp, max_temp):
        self.min_temp = min_temp
        self.max_temp = max_temp
    def setup_callback(self, cb):
        self._callback = cb
    def get_report_time_delta(self):
        return self.report_time
    def _sample_temp(self, eventtime):
        with self._lock:
            temp = self.temp
        if temp < self.min_temp:
            self.printer.invoke_shutdown(
                "DS18B20 temperature %0.1f below minimum temperature of %0.1f."
                % (temp, self.min_temp))
        if temp > self.max_temp:
            self.printer.invoke_shutdown(
                "DS18B20 temperature %0.1f above maximum temperature of %0.1f."
                % (temp, self.max_temp))
        mcu = self.printer.lookup_object('mcu')
        measured_time = self.reactor.monotonic()
        self._callback(mcu.estimated_print_time(measured_time), temp)
        return eventtime + self.report_time
    def get_status(self, eventtime):
        with self._lock:
            temp = self.temp
        return {
            'temperature': round(temp, 2),
        }

def load_config(config):
    # Register sensor
    pheaters = config.get_printer().load_object(config, "heaters")
    pheaters.add_sensor_factory("DS18B20_HOST", DS18B20)
