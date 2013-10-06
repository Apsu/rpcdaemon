import copy
from ConfigParser import RawConfigParser


# Indexable config parser
class Config(RawConfigParser):
    def __init__(self, path, section='DEFAULT'):
        self.path = path
        RawConfigParser.__init__(self)  # Old-style class
        if self.read(path):
            if section in self.sections():
                self._config = dict(self.items(section))
            else:
                raise KeyError('No section %s in config file %s' % (section, path))
        else:
            raise IOError('Failed to parse config file %s' % path)

    def __getitem__(self, item):
        return self._config[item]

    def section(self, section=None):
        if not section or not section in self.sections():
            raise KeyError('No section %s in config file %s' % (section, self.path))

        new = copy.deepcopy(self)
        new._config = dict(new.items(section))
        return new
