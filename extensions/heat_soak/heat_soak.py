import logging

class HeatSoak:
    def __init__(self, config):

        self.chamber_sensor_name = config.get("chamber_sensor", default=None)

        self.printer = config.get_printer()

        self.printer.register_event_handler("klippy:ready", self._klippy_ready)
        self.printer.register_event_handler("klippy:shutdown", self._klippy_shutdown)
        
        self.display_status = None
        self.bed = None
        self.extruder = None
        self.chamber = None

        self.baseline_bed_temp = None
        self.baseline_extruder_temp = None
        self.baseline_chamber_temp = None

        self.wait_sec = None
        self.wait_start_eventtime = None

        gcode = self.printer.lookup_object("gcode")
        gcode.register_command("HEAT_SOAK_BASELINE", self.cmd_HEAT_SOAK_BASELINE, desc=self.cmd_HEAT_SOAK_BASELINE_desc)
        gcode.register_command("HEAT_SOAK_WAIT", self.cmd_HEAT_SOAK_WAIT, desc=self.cmd_HEAT_SOAK_WAIT_desc)

    cmd_HEAT_SOAK_BASELINE_desc = ('Collect baseline values for heat soaking')
    
    def cmd_HEAT_SOAK_BASELINE(self, gcmd):
        self._log(f"HEAT_SOAK_BASELINE {gcmd.get_command_parameters()}")
        self.baseline_bed_temp = self._get_bed_temp()
        self.baseline_extruder_temp = self._get_extruder_temp()
        self.baseline_chamber_temp = self._get_chamber_temp()

        self._log(f"baseline_bed_temp: {self.baseline_bed_temp}")
        self._log(f"baseline_extruder_temp: {self.baseline_extruder_temp}")
        self._log(f"baseline_chamber_temp: {self.baseline_chamber_temp}")

    cmd_HEAT_SOAK_WAIT_desc = ('Wait for heat soak to complete. FOR=<bed|extruder|chamber> TEMP=<target> START_TEMP=<optional starting temp>')
    
    def cmd_HEAT_SOAK_WAIT(self, gcmd):
        self._log(f"HEAT_SOAK_WAIT {gcmd.get_command_parameters()}")

        gcode = self.printer.lookup_object("gcode")

        if not self.baseline_bed_temp or not self.baseline_extruder_temp or not self.baseline_chamber_temp:
            raise gcode.error("HEAT_SOAK_BASELINE should be called when starting a print, baseline was not collected")

        wait_for = gcmd.get("FOR")
        wait_temp = gcmd.get_float("TEMP")

        if wait_for not in ['bed', 'extruder', 'chamber']:
            raise self.printer.lookup_object("gcode").error("FOR is invalid, it must be bed|extruder|chamber")
        
        if wait_for == 'chamber' and not self.baseline_chamber_temp:
            raise gcode.error("Can't heat soak using 'chamber' because no chamber sensor was registered")

        diff = 0
        ms_per_degree = 0.0
        if wait_for == 'bed':
            start_temp = gcmd.get_float("START_TEMP", self.baseline_bed_temp)
            diff = wait_temp - start_temp
            ms_per_degree = 16000.0
        elif wait_for == 'extruder':
            start_temp = gcmd.get_float("START_TEMP", self.baseline_extruder_temp)
            diff = wait_temp - start_temp
            ms_per_degree = 500.0
        elif wait_for == 'chamber':
            start_temp = gcmd.get_float("START_TEMP", self.baseline_chamber_temp)
            diff = wait_temp - start_temp
            ms_per_degree = 10000.0

        wait_sec = (diff * ms_per_degree) / 1000.0
        if wait_sec <= 0.0:
            gcode.respond_info(f"soak time is <= 0, no heat soak necessary")
            return
        self.wait_sec = wait_sec

        if self.display_status:
            self.display_status.message = f"Heat soaking {wait_for}: {round(self.wait_sec)}s remaining..."

        def check(eventtime):
            if not self.wait_start_eventtime:
                self.wait_start_eventtime = eventtime
                return True
            sec_left = round(self.wait_sec - (eventtime - self.wait_start_eventtime))
            if sec_left % 10 == 0:
                self._log(f"heat soak {sec_left}")
                if self.display_status:
                    self.display_status.message = f"Heat soaking {wait_for}: {round(sec_left)}s remaining..."
            return sec_left > 0

        self.printer.wait_while(check)
        self.wait_sec = None
        self.wait_start_eventtime = None

    def _log(self, message):
        logging.info(f"[heat_soak] {message}")

    def _klippy_ready(self):
        self._log("klippy:ready")
        self._log(f"chamber_sensor={self.chamber_sensor_name}")

        self.bed = self.printer.lookup_object("heater_bed").heater
        self.display_status = self.printer.lookup_object("display_status", default = None)

        # TODO: What about multiple toolheads?
        self.extruder = self.printer.lookup_object("toolhead").get_extruder().get_heater()
        if self.chamber_sensor_name:
            self.chamber = self.printer.lookup_object(f"temperature_sensor {self.chamber_sensor_name}")

    def _klippy_shutdown(self):
        self._log("klippy:shutdown")

    def _get_bed_temp(self, eventtime = None):
        if eventtime == None:
            eventtime = self.printer.reactor.monotonic()
        return round(self.bed.get_temp(eventtime)[0], 2)

    def _get_extruder_temp(self, eventtime = None):
        if eventtime == None:
            eventtime = self.printer.reactor.monotonic()
        return round(self.extruder.get_temp(eventtime)[0], 2)

    def _get_chamber_temp(self, eventtime = None):
        if not self.chamber:
            return None
        if eventtime == None:
            eventtime = self.printer.reactor.monotonic()
        return round(self.chamber.get_temp(eventtime)[0], 2)

def load_config(config):
    return HeatSoak(config)
