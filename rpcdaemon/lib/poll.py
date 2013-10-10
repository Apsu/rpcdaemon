from threading import Event, Thread


class Poll(object):
    def __init__(self, interval):
        self.interval = interval

    def __call__(self, func):
        def wrap(*args, **kwargs):
            event = Event()

            def loop():
                while not event.wait(self.interval):
                    func(*args, **kwargs)

            thread = Thread(target=loop)
            thread.daemon = True
            thread.start()
            return event
        return wrap
