import logging

class ChamberHeater:
    def __init__(self, config):
        self.name = config.get_name().split()[1]
        self.temp_sensor_name = config.get("sensor")
        self.heater_name = config.get("heater")
        self.period = config.getfloat("period", 5.0)

        self.printer = config.get_printer()
        
        logging.info(f"[chamber_heater {self.name}], sensor={self.temp_sensor_name}, heater={self.heater_name}")

        self.printer.register_event_handler("klippy:ready", self._klippy_ready)
        self.printer.register_event_handler("klippy:shutdown", self._klippy_shutdown)

        gcode = self.printer.lookup_object("gcode")
        gcode.register_mux_command

    def _klippy_ready(self):
        logging.info(f"[chamber_heater {self.name}] klippy:ready")

        self.temp_sensor = self.printer.lookup_object(f"temperature_sensor {self.temp_sensor_name}")
        self.heater = self.printer.lookup_object(f"heater_generic {self.heater_name}")

        reactor = self.printer.get_reactor()
        self.timer = reactor.register_timer(self._reactor_timer_event, reactor.monotonic() + self.period)

    def _klippy_shutdown(self):
        logging.info(f"[chamber_heater {self.name}] klippy:shutdown")
        reactor = self.printer.get_reactor()
        if self.timer:
            reactor.unregister_timer(self.timer)

    def _reactor_timer_event(self, eventtime):
        self.inside_timer = True
        logging.info(f"[chamber_heater {self.name}] timer event {self.temp_sensor.get_temp(eventtime)}")
        self.inside_timer = False
        return eventtime + self.period

def load_config_prefix(config):
    return ChamberHeater(config)

'''
        def check(eventtime):
            self.gcode.respond_raw(self._get_temp(eventtime))
            return heater.check_busy(eventtime)

        self.printer.wait_while(check)
'''
