import copy
from ConfigParser import RawConfigParser


# Indexable config parser
class Config(RawConfigParser):
    def __init__(self, path, section='DEFAULT'):
        self.path = path
        RawConfigParser.__init__(self)  # Old-style class
        if self.read(path):
            self._config = dict(self.items(section))
        else:
            raise IOError('Failed to parse config file %s' % path)

    def __getitem__(self, item):
        return self._config[item]

    def section(self, section='DEFAULT'):
        return Config(self.path, section)

    def get(self, item, default):
        return self._config[item] if item in self._config else default
