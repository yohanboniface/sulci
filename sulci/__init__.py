
__version_info__ = {
    'major': 0,
    'minor': 1,
    'micro': 0,
    'releaselevel': 'alpha',
    'serial': 0
}

def get_version():
    vers = ["%(major)i.%(minor)i" % __version_info__, ]

    if __version_info__['micro']:
        vers.append(".%(micro)i" % __version_info__)
    if __version_info__['releaselevel'] != 'final':
        vers.append('%(releaselevel)s%(serial)i' % __version_info__)
    return '.'.join(vers)

__version__ = get_version()

#def get_model_for_descriptor():
#    try:
#        return loading.get_model(settings.SULCI_DESCRIPTOR_APP_NAME, settings.SULCI_DESCRIPTOR_MODEL_NAME)
#    except:
#        return None # Fail silently for now.

#descriptor_model = get_model_for_descriptor()
try:
    from django.db.models import loading
    from django.conf import settings
except ImportError: # setup.py import sulci...
    print "Warning. It seems that Django isn't configured properly."
else:
    try:
        def get_model_for_content():
            return loading.get_model(settings.SULCI_CLI_CONTENT_APP_NAME,
                                     settings.SULCI_CLI_CONTENT_MODEL_NAME)
        content_model = get_model_for_content()

        def get_manager_for_content():
            name = getattr(settings, 'SULCI_CLI_CONTENT_MANAGER_NAME', 'objects')
            manager = getattr(content_model, name)
            return manager
        content_manager = get_manager_for_content()
    except AttributeError:
        # No settings where setted (possible, is command line and training are no
        # planed.
        print "Missing settings : command line and training will no be usable."
        content_model = None
        content_manager = None

