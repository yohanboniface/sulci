# -*- coding: utf-8 -*-
import json

from django.core.urlresolvers import reverse_lazy
from django.http import HttpResponse
from django import forms
from django.views.generic import FormView

from sulci.textmining import SemanticalTagger
from sulci.log import sulci_logger, MemoryStorageHandler, HTMLColorFormatter


class SulciForm(forms.Form):
    CORPUS = (
        ("liberation", u"Libération"),
        ("lemondediplo", u"le Monde diplomatique"),
        ("rezo", u"Rezo.net"),
    )
    content = forms.CharField(widget=forms.Textarea, help_text="(string, mantatory) The content to process")
    min_score = forms.IntegerField(initial=10, required=False, help_text="(int, default=10) Min score of the descriptors to return")
    limit = forms.IntegerField(initial=15, required=False, help_text="(int, default=15) Limit number of returnerd descriptors")
    corpus = forms.ChoiceField(choices=CORPUS, required=False, help_text="(string, default=liberation) Corpus to use. Available choices: liberation, lemondediplo, rezo")
    keyentities = forms.BooleanField(required=False, help_text="(boolean, default=false) Return also the extracted entities from the content")
    debug = forms.BooleanField(required=False, help_text="(boolean, default=false) Return a HTML debug info")

    def clean_min_score(self):
        min_score = self.cleaned_data.get("min_score", None)
        if not min_score:
            self.cleaned_data["min_score"] = 10
        return self.cleaned_data["min_score"]

    def clean_limit(self):
        limit = self.cleaned_data.get("limit", None)
        if not limit:
            self.cleaned_data["limit"] = 15
        return self.cleaned_data["limit"]

    def clean_corpus(self):
        corpus = self.cleaned_data.get("corpus", None)
        if not corpus:
            self.cleaned_data["corpus"] = "liberation"
        return self.cleaned_data["corpus"]

    def clean_keyentities(self):
        keyentities = self.cleaned_data.get("keyentities", None)
        if not keyentities:
            self.cleaned_data["keyentities"] = False
        return self.cleaned_data["keyentities"]

    def clean_debug(self):
        debug = self.cleaned_data.get("debug", None)
        if not debug:
            self.cleaned_data["debug"] = False
        return self.cleaned_data["debug"]


class DemoView(FormView):

    form_class = SulciForm
    template_name = "django_sulci/demo.html"
    success_url = reverse_lazy("sulci_demo")


class WSView(object):

    def __call__(self, request, *args, **kwargs):
        c = {}
        if request.method == "POST":
            form = SulciForm(request.POST)
            if form.is_valid():
                print form.cleaned_data
                content = form.cleaned_data["content"]
                limit = form.cleaned_data["limit"]
                min_score = form.cleaned_data["min_score"]
                if form.cleaned_data["debug"]:
                    debug = []
                    handler = MemoryStorageHandler(10, target=debug)
                    formatter = HTMLColorFormatter("%(message)s")
                    handler.setFormatter(formatter)
                    sulci_logger.addHandler(handler)
                S = SemanticalTagger(content)
                descriptors = [(unicode(d), round(score, 2)) for d, score in S.get_descriptors(min_score)[:limit]]
                if form.cleaned_data['keyentities']:
                    keyentities = [(unicode(k), round(k.frequency_relative_pmi_confidence, 2)) for k in S.keyentities]
                else:
                    keyentities = None
                c = {
                    "descriptors": descriptors,
                    "keyentities": keyentities,
                }
                if form.cleaned_data["debug"]:
                    S.debug()
                    handler.flush()
                    c["debug"] = [handler.format(d) for d in debug]
            else:
                c = {'errors': form.errors}
        else:
            form = SulciForm()
            for field_name, field in form.fields.iteritems():
                c[field_name] = field.help_text
        return HttpResponse(json.dumps(c), content_type="application/json")
