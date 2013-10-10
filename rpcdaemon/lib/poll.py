from threading import Event, Thread


class Poll(object):
    def __init__(self, interval, func, *args, **kwargs):
        interval = interval
        event = Event()

        def loop():
            while not event.wait(interval):
                func(*args, **kwargs)

        thread = Thread(target=loop)
        thread.daemon = True
        thread.start()
