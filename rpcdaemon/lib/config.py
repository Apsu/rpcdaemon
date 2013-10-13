import copy
from ConfigParser import SafeConfigParser


# Indexable config parser
class Config(SafeConfigParser):
    def __init__(self, path, section='DEFAULT'):
        self._path = path
        self._section = section
        SafeConfigParser.__init__(self)
        if self.read(path):
            self._config = dict(self.items(section))
        else:
            raise IOError('Failed to parse config file %s' % path)

    def __getitem__(self, item):
        try:
            return self.get(self._section, item)
        except:
            raise IndexError()

    def section(self, section):
        return Config(self._path, section)
