import logging

class ChamberHeater:
    def __init__(self, config):
        self.name = config.get_name().split()[1]
        self.temp_sensor_name = config.get("sensor")
        self.heater_name = config.get("heater")
        
        self.printer = config.get_printer()
        self.reactor = self.printer.get_reactor()
        
        logging.info(f"[chamber_heater {self.name}], sensor={self.temp_sensor_name}, heater={self.heater_name}")

        self.printer.register_event_handler("klippy:ready", self._klippy_ready)

    def _klippy_ready(self):
        logging.info(f"[chamber_heater {self.name}] klippy:ready")

        self.temp_sensor = self.printer.lookup_object(self.temp_sensor_name)

        waketime = self.reactor.monotonic() + 5
        self.timer_handler = self.reactor.register_timer(self._reactor_timer_event, waketime)

    def _reactor_timer_event(self, eventtime):
        self.inside_timer = True
        logging.info(f"[chamber_heater {self.name}] timer event {self.temp_sensor.get_temp(eventtime)}")
        self.inside_timer = False
        return eventtime + 5

def load_config_prefix(config):
    return ChamberHeater(config)
