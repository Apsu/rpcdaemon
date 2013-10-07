import logging


# Thin wrapper (not so) cleverly straddling logging.Logger namespace
class Logger(logging.Logger):
    def __init__(
            self,
            name='logger',
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            path='logger.log',
            handler=None
    ):
        # Call super
        logging.Logger.__init__(self, name, level)
        self.handler = handler if handler else logging.FileHandler(path)
        self.handler.setFormatter(logging.Formatter(format))
        self.addHandler(self.handler)
