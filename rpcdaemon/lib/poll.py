from threading import Event, Thread


class Poll(object):
    def __init__(self, interval, func, *args, **kwargs):
        self.interval = interval
        self.event = Event()

        def loop():
            while not self.event.wait(self.interval):
                func(*args, **kwargs)

        self.thread = Thread(target=loop)
        self.thread.daemon = True  # Daemon thread
        self.thread.start()
