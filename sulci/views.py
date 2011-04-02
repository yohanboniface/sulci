# -*- coding: utf-8 -*-
import logging

from datetime import date, timedelta

from django.views.generic.simple import direct_to_template
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext
from django.http import HttpResponse, Http404, HttpResponseBadRequest
from django.conf import settings
from django import forms

from sulci.textmining import SemanticalTagger
from sulci.log import sulci_logger, MemoryStorageHandler, HTMLColorFormatter

def demo(request, *args, **kwargs):
    """
    A simple demo view.
    """
    class SulciForm(forms.Form):
        content = forms.CharField(widget=forms.Textarea)
        debug = forms.BooleanField(required=False)
    if request.method == "POST":
        form = SulciForm(request.POST)
        c = {}
        if form.is_valid():
            content = form.cleaned_data["content"]
            if form.cleaned_data["debug"]:
                debug = []
                handler = MemoryStorageHandler(10, target=debug)
                formatter = HTMLColorFormatter("%(message)s")
                handler.setFormatter(formatter)
                sulci_logger.addHandler(handler)
            S = SemanticalTagger(content)
            c = {"content": content, "descriptors": S.descriptors, "form": form}
            if form.cleaned_data["debug"]:
                S.debug()
                handler.flush()
                c["sulci_debug"] = [handler.format(d) for d in debug]
    else:
        form = SulciForm()
        c = {"form": form}
    return direct_to_template(request, 
                              extra_context=c,
                              context_instance=RequestContext(request), 
                              template="sulci/demo.html")

