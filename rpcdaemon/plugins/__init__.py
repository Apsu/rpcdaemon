import pkgutil


def plugins():
    print list(pkgutil.iter_modules(['plugins']))
    return [
        plugin[1] for plugin in
        pkgutil.iter_modules(['plugins/'])
        if plugin[2]
    ]
