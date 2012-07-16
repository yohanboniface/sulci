# -*- coding: utf-8 -*-
from django.db.models import Model, loading
from django.conf import settings

def get_model_for_content():
    return loading.get_model(settings.SULCI_CLI_CONTENT_APP_NAME, settings.SULCI_CLI_CONTENT_MODEL_NAME)

def get_manager_for_content(inst):
    name = getattr(settings, 'SULCI_CLI_CONTENT_MANAGER_NAME', 'objects')
    manager = getattr(get_model_for_content(), name)
    return manager

content_model = get_model_for_content()

