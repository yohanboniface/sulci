# -*- coding:utf-8 -*-

import os
import re
import threading

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

# Make the current db thread localised
CURRENT = threading.local()
CURRENT.DB = DEFAULT_DATABASE


def get_current_db_name():
    if hasattr(CURRENT, "DB"):
        return CURRENT.DB
    else:
        return DEFAULT_DATABASE
