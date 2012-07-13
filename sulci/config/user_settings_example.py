"""
You must define an environnement variable pointing to your config module.
For example: $ export SULCI_CONFIG_MODULE="diplo.sulci_config"
Obviously, the module must be in the PYTHONPATH also.
"""

def content_model_getter(primary_key):
    # this should return a instance from the primary_key attribute
    pass

def descriptors_getter(inst):
    # This should return a list of descriptors (str)
    # It's used only for the training part
    pass