import logging

class HeatSoak:
    def __init__(self, config):

        self.chamber_sensor_name = config.get("chamber_sensor", default=None)

        self.printer = config.get_printer()

        self.printer.register_event_handler("klippy:ready", self._klippy_ready)
        self.printer.register_event_handler("klippy:shutdown", self._klippy_shutdown)
        
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

        # self.target_chamber_temp = gcmd.get_float("TEMP")
        
        # reactor = self.printer.get_reactor()
        # if self.adjust_timer:
        #     reactor.unregister_timer(self.adjust_timer)

        # if self._get_chamber_temp(reactor.monotonic()) < self.target_chamber_temp:
        #     self.target_temp_reached = False
        #     self._set_heater_temp(self.max_temp)
        # else:
        #     self.target_temp_reached = True

        # self.adjust_timer = reactor.register_timer(self._adjust_temp_timeout, reactor.monotonic() + self.period)


    cmd_HEAT_SOAK_WAIT_desc = ('Wait for heat soak to complete. FOR=<bed|extruder|chamber> TEMP=<target>')
    
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
            diff = wait_temp - self.baseline_bed_temp
            ms_per_degree = 16000.0
        elif wait_for == 'extruder':
            diff = wait_temp - self.baseline_extruder_temp
            ms_per_degree = 500.0
        elif wait_for == 'chamber':
            diff = wait_temp - self.baseline_chamber_temp
            ms_per_degree = 10000.0

        wait_sec = (diff * ms_per_degree) / 1000.0
        if wait_sec <= 0.0:
            gcode.respond_info(f"soak time is <= 0, no heat soak necessary")
            return
        self.wait_sec = wait_sec

        #self.printer.state_message = f"Heat soaking {wait_for} for {round(self.wait_sec)}s..."

        def check(eventtime):
            if not self.wait_start_eventtime:
                self.wait_start_eventtime = eventtime
                return True
            sec_left = round(self.wait_sec - (eventtime - self.wait_start_eventtime))
            if sec_left % 10 == 0:
                self._log(f"heat soak {sec_left}")
            return sec_left > 0

        self.printer.wait_while(check)
        self.wait_sec = None
        self.wait_start_eventtime = None

    # cmd_CHAMBER_HEAT_WAIT_desc = ('Wait for the build chamber temperature to reach the desired value')
    
    # def cmd_CHAMBER_HEAT_WAIT(self, gcmd):
    #     self._log(f"CHAMBER_HEAT_WAIT {gcmd.get_command_parameters()}")
    #     wait_chamber_temp = gcmd.get_float("TEMP", self.target_chamber_temp, minval = 30.0, maxval = self.target_chamber_temp)
    #     gcode = self.printer.lookup_object("gcode")
    #     gcode.respond_info(f"Waiting for chamber temp to reach {wait_chamber_temp}")
        
    #     def check(eventtime):
    #         return self._get_chamber_temp(eventtime) < wait_chamber_temp

    #     self.printer.wait_while(check)

    # def _get_chamber_temp(self, eventtime):
    #     temp, _ = self.temp_sensor.get_temp(eventtime)
    #     return round(temp, 2)
    
    # def _set_heater_temp(self, degrees):
    #     if self.heater.target_temp != degrees:
    #         self.heater.set_temp(degrees)

    # def _adjust_temp_timeout(self, eventtime):
    #     current_temp = self._get_chamber_temp(eventtime)
    #     if current_temp >= self.target_chamber_temp:
    #         self.target_temp_reached = True

    #     difference = round(current_temp - self.target_chamber_temp, 2)
        
    #     # If the target temp has not been reached, keep the heater on full-blast
    #     set_temp = self.max_temp
        
    #     if self.target_temp_reached:
    #         if difference <= -2:
    #             set_temp = self.max_temp
    #         elif difference <= -0.5:
    #             set_temp = self.target_chamber_temp + (self.max_temp - self.target_chamber_temp) / 2
    #         elif difference <= 0.5:
    #             set_temp = self.target_chamber_temp
    #         elif difference <= 2:
    #             set_temp = self.target_chamber_temp - 10
    #         else:
    #             set_temp = 0

    #     self._set_heater_temp(set_temp)
    #     self._log(f"_adjust_temp_timout: reached={self.target_temp_reached}, current={current_temp}, target={self.target_chamber_temp}, difference={difference}, set={set_temp}")
     
    #     return eventtime + self.period

    def _log(self, message):
        logging.info(f"[heat_soak] {message}")

    def _klippy_ready(self):
        self._log("klippy:ready")
        self._log(f"chamber_sensor={self.chamber_sensor_name}")

        self.bed = self.printer.lookup_object("heater_bed").heater

        # TODO: What about multiple toolheads?
        self.extruder = self.printer.lookup_object("toolhead").get_extruder().get_heater()
        if self.chamber_sensor_name:
            self.chamber = self.printer.lookup_object(f"temperature_sensor {self.chamber_sensor_name}")

    def _klippy_shutdown(self):
        self._log("klippy:shutdown")
        # if self.adjust_timer:
        #     reactor = self.printer.get_reactor()
        #     reactor.unregister_timer(self.adjust_timer)

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
