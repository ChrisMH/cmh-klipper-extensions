import logging

class Buddy:
    def __init__(self, config):
        name = config.get_name().split()[1]
        logging.info(f"Buddy.__init__: {name}")

def load_config_prefix(config):
    return Buddy(config)
