import logging

class Buddy:
    def __init__(self, config):
        self.name = config.get_name().split()[1]
        self.printer = config.get_printer()
        self.reactor = self.printer.get_reactor()

        logging.info(f"[buddy {self.name}] Initialized")

        self.printer.register_event_handler("klippy:ready", self._klippy_ready)

    def _klippy_ready(self):
        logging.info(f"[buddy {self.name}] klippy:ready")
        waketime = self.reactor.monotonic() + 5
        self.timer_handler = self.reactor.register_timer(self._reactor_timer_event, waketime)

    def _reactor_timer_event(self, eventtime):
        self.inside_timer = True
        logging.info(f"[buddy {self.name}] timer event")
        self.inside_timer = False
        return eventtime + 5

def load_config_prefix(config):
    return Buddy(config)
