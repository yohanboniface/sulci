import os
import re

# import default
from sulci.config.default import *

user_settings = __import__(
    os.environ["SULCI_CONFIG_MODULE"],
    fromlist=["SULCI_CONFIG_MODULE"]
)

# Override with user ones
for attr in dir(user_settings):
    if re.search('^[a-zA-Z]', attr):
        globals()[attr] = getattr(user_settings, attr)