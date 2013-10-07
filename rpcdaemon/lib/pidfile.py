import os


class PIDFile():
    def __init__(self, path):
        if not path:
            raise IOError('File not found. Please specify PID file path.')

        self.path = path

    def __enter__(self):
        if not os.path.exists(self.path):
            # Create it
            with open(self.path, 'w') as pidfile:
                pidfile.write(str(os.getpid()) + '\n')
        else:
            # Open for read/write, so we can do either
            with open(self.path, 'rw+') as pidfile:
                # Get PID from file, stripping whitespace and leading 0s
                pid = str(int(pidfile.readline().strip()))
                # pidfile and process exist
                if pid and os.path.exists('/proc/' + pid):
                    raise SystemExit('Daemon already running.')
                else:
                    # Clear and write our PID
                    pidfile.seek(0)
                    pidfile.write(str(os.getpid()) + '\n')
                    pidfile.truncate()

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # If pidfile exists here we wrote it; kill it
        if os.path.exists(self.path):
            os.remove(self.path)

        # Succeeded at exiting; don't suppress any bubbled exceptions
        return False
