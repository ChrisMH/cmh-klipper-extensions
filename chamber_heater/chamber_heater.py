import logging

class ChamberHeater:
    def __init__(self, config):
        self.name = config.get_name().split()[1]

        self.temp_sensor_name = config.get("sensor")
        self.heater_name = config.get("heater")
        self.period = config.getfloat("period", 5.0)
        self.max_temp = config.getfloat("max_temp")

        self.printer = config.get_printer()
        
        self._log(f"sensor={self.temp_sensor_name}, heater={self.heater_name}, period={self.period}, max_temp={self.max_temp}")

        self.printer.register_event_handler("klippy:ready", self._klippy_ready)
        self.printer.register_event_handler("klippy:shutdown", self._klippy_shutdown)
        
        self.target_chamber_temp = None
        self.adjust_timer = None

        gcode = self.printer.lookup_object("gcode")
        gcode.register_mux_command("CHAMBER_HEAT_ON", "HEATER", self.name, self.cmd_CHAMBER_HEAT_ON, self.cmd_CHAMBER_HEAT_ON_desc)
        gcode.register_mux_command("CHAMBER_HEAT_OFF", "HEATER", self.name, self.cmd_CHAMBER_HEAT_OFF, self.cmd_CHAMBER_HEAT_OFF_desc)
        gcode.register_mux_command("CHAMBER_HEAT_WAIT", "HEATER", self.name, self.cmd_CHAMBER_HEAT_WAIT, self.cmd_CHAMBER_HEAT_WAIT_desc)

    cmd_CHAMBER_HEAT_ON_desc = ('Turn the chamber heater on and start the process of heating up the build chamber')
    
    def cmd_CHAMBER_HEAT_ON(self, gcmd):
        self._log(f"CHAMBER_HEAT_ON {gcmd.get_command_parameters()}")
        self.target_chamber_temp = gcmd.get_float("TEMP")
        
        reactor = self.printer.get_reactor()
        if self.adjust_timer:
            reactor.unregister_timer(self.adjust_timer)
        self.adjust_timer = reactor.register_timer(self._adjust_temp_timeout, reactor.monotonic() + self.period)


    cmd_CHAMBER_HEAT_OFF_desc = ('Turn the chamber heater off')
    
    def cmd_CHAMBER_HEAT_OFF(self, gcmd):
        self._log(f"CHAMBER_HEAT_OFF {gcmd.get_command_parameters()}")
        self.target_chamber_temp = None

        if self.adjust_timer:
            reactor = self.printer.get_reactor()
            reactor.unregister_timer(self.adjust_timer)
            self.adjust_timer = None


    cmd_CHAMBER_HEAT_WAIT_desc = ('Wait for the build chamber temperature to reach the desired value')
    
    def cmd_CHAMBER_HEAT_WAIT(self, gcmd):
        self._log(f"CHAMBER_HEAT_WAIT {gcmd.get_command_parameters()}")
        wait_chamber_temp = gcmd.get_float("TEMP", self.target_chamber_temp, minval = 30.0, maxval = self.target_chamber_temp)
        gcode = self.printer.lookup_object("gcode")
        gcode.respond_info(f"Waiting for chamber temp to reach {wait_chamber_temp}")
        
        def check(eventtime):
            return self._get_chamber_temp(eventtime) < wait_chamber_temp

        self.printer.wait_while(check)

    def _get_chamber_temp(self, eventtime):
        temp, _ = self.temp_sensor.get_temp(eventtime)
        return round(temp, 2)
    
    def _set_heater_temp(self, degrees):
        self.heater.set_temp(degrees)

    def _adjust_temp_timeout(self, eventtime):
        self.inside_timer = True
        self._log(f"current chamber temp {self.temp_sensor.get_temp(eventtime)}")
        self.inside_timer = False
        return eventtime + self.period

    def _log(self, message):
        logging.info(f"[chamber_heater {self.name}] {message}")

    def _klippy_ready(self):
        self._log("klippy:ready")

        self.temp_sensor = self.printer.lookup_object(f"temperature_sensor {self.temp_sensor_name}")
        self.heater = self.printer.lookup_object(f"heater_generic {self.heater_name}")

    def _klippy_shutdown(self):
        self._log("klippy:shutdown")
        if self.adjust_timer:
            reactor = self.printer.get_reactor()
            reactor.unregister_timer(self.adjust_timer)



def load_config_prefix(config):
    return ChamberHeater(config)

'''
        def check(eventtime):
            self.gcode.respond_raw(self._get_temp(eventtime))
            return heater.check_busy(eventtime)

        self.printer.wait_while(check)
'''
