# -*- coding:Utf-8 -*-

import re
import codecs
import os

from django.db import models, transaction
from django.db.utils import IntegrityError

from sulci.textutils import tokenize_text, lev
from sulci.base import RetrievableObject
from sulci.utils import save_to_file, get_dir

class Thesaurus(object):

    def __init__(self, path="thesaurus.txt"):
        self.descriptors = Descriptor.objects.all()
    
    def __contains__(self, item):
        """
        TODO.
        """
        try:
            d = self[item]
            return True
        except Descriptor.DoesNotExist:
            return False
    
    def __iter__(self): 
        return self.descriptors.__iter__()
    
    def __getitem__(self, key):
        return Descriptor.objects.get(name=unicode(key))
    
    def normalize_item(self, item):
        from textmining import KeyEntity#Sucks...
        if isinstance(item, KeyEntity):
            tup = tuple([unicode(t) for t in item.stemms])
        elif isinstance(item, list):
            tup = tuple(item)
        elif isinstance(item, (unicode, str)):
            tup = tuple(item.split())
        else:
            tup = item
        return tuple(sorted(tup))

    @property
    def triggers(self):
        if self._triggers is None:#cached and lazy
            self._triggers = set()
            self.load_triggers()
        return self._triggers
    
    def load_triggers(self):
        sulci_logger.debug("Loading triggers...", "YELLOW", True)
        f = codecs.open(get_dir() + "corpus/triggers.trg", "r", "utf-8")
        for idx, line in enumerate(f.readlines()):
            #TODO check line validity
            t, created = Trigger.get_or_create(line, self, parent=self, original=line)
            self._triggers.add(t)
        f.close()
    
    @classmethod
    def reset_triggers(self):
        """
        For full training, we need to remove previous triggers.
        """
        save_to_file("corpus/triggers.trg", "")

class Descriptor(models.Model): 
    """
    Entries of the Thesaurus.
    """
    parent = models.ForeignKey('self', 
        blank=True, 
        null=True, 
        related_name="children")
    name = models.CharField(max_length=200, db_index=True)
    description = models.TextField(blank=True, null=True)
    is_alias_of = models.ForeignKey('self', 
                      blank=True, 
                      null=True, 
                      related_name="aliases", 
                      help_text="If this descriptor is an alias of another."
                  )
    
    def __init__(self, *args, **kwargs):
        self._max_weight = None
        super(Descriptor, self).__init__(*args, **kwargs)
    
    @property
    def original(self):
        # Retrocompatibility
        return self.name
    
    def __unicode__(self):
        return unicode(self.original)
    
    @property
    def max_weight(self):
        if self._max_weight is None: # Thread cache
            try:
                #Ordered by -weight by default
                self._max_weight = self.triggertodescriptor_set.all()[0].weight
            except TriggerToDescriptor.DoesNotExist:
                # Should not occur.
                self._max_weight = 0
        return self._max_weight
    
    @property
    def primeval(self):
        """
        Returns the primeval descriptor when self is alias of another.
        """
        if self.is_alias_of is None:
            return self
        return self.is_alias_of.primeval

class TriggerToDescriptor(models.Model):
    """
    This is the "synapse" of the trigger to descriptor relation.
    """
    descriptor = models.ForeignKey(Descriptor, db_index=True)
    trigger = models.ForeignKey("Trigger", db_index=True)
    weight = models.FloatField(default=0, db_index=True)
    
    @property
    def pondered_weight(self):
        """
        Give the weight of the relation, relative to the max weight of the
        trigger and the max weight of the descriptor.
        """
        # current weigth relative to trigger max weight
        weight = self.weight / self.trigger.max_weight
        # current weight relative to descriptor max weight
        weight *= self.weight / self.descriptor.max_weight
#        # current weight relative to trigger count
#        # we use logarithm to limit negative impact for very common triggers
#        weight *= math.log(self.weight) / math.log(self.trigger.count)
#        # current weight relative to descriptor occurrences in training
#        # Using log to limit impact
#        weight *= \
#           math.log(self.weight) / math.log(self.descriptor.trained_occurrences)
        return weight
    
    class Meta:
        unique_together = ("descriptor", "trigger")
        ordering = ["-weight"]

    def __unicode__(self):
        return u"%s =(%f)=> %s" % (self.trigger, self.weight, self.descriptor)


class Trigger(models.Model):
    """
    The trigger is a keyentity who suggest some descriptors when in a text.
    It is linked to one or more descriptors, and the distance of the link
    between the trigger and a descriptor is stored in the relation.
    This score is populated during the sementical training.
    """
    original = models.CharField(max_length=500, db_index=True, unique=True)
    count = models.IntegerField(default=0,blank=True)
    descriptors = models.ManyToManyField("Descriptor", 
                through="TriggerToDescriptor", 
                blank=True, 
                null=True)    
    def __init__(self, *args, **kwargs):
        self._max_weight = None
        # We cache relatins to descriptors. But during training, some other processes
        # could create and modify relations. This is a potential source of
        # bad behaviour, but at the moment I prefer to have good performance
        # cause I launch very often the script for testing it...
        self._cached_descriptors = None
        self._cached_synapses = None
        super(Trigger, self).__init__(*args, **kwargs)
#        self.id = pk#Tuple of original string
#        self.original = u" ".join(pk)
#        self.parent = kwargs["parent"]
#        self._descriptors = {}
#        self.init_descriptors(**kwargs)
    
    @property
    def _descriptors(self):
        if self._cached_descriptors is None:
            self._cached_descriptors = list(self.descriptors.all())
        return self._cached_descriptors
    
    @property
    def _synapses(self):
        if self._cached_synapses is None:
            self._cached_synapses = list(self.triggertodescriptor_set.select_related().all()[:20])
        return self._cached_synapses
    
    def __unicode__(self):
        return unicode(self.original)
    
    def __contains__(self, key):
        return key in self._descriptors
    
    def __setitem__(self, key, value):
        if not isinstance(key, Descriptor):
            raise ValueError("Key must be Descriptor instance, got %s (%s) instead" 
                                                        % (str(key), type(key)))
        # Flush descriptors cache
        self._cached_descriptors = None
        # As we cache, and some other process could have created the 
        # relation between this trigger and this descriptor
        # we catch IntegrityErrors. Maybe a get_or_create should do the job ?
        try:
            return TriggerToDescriptor.objects.get_or_create(descriptor=key, 
                                                      trigger=self,
                                                      weight=value)
        except IntegrityError:
            # Another process has created the relation.
            # It we return self[key], we get a DatabaseError from psycho...
            # I've tried a transaction.rollback(), but got an error too.
            pass
    
    def __getitem__(self, key):
        return TriggerToDescriptor.objects.get(descriptor=key, trigger=self)
    
#    def __delitem__(self, key):
#        return self._descriptors.__delitem__(key)
    
    def __iter__(self):
        return self._synapses.__iter__()
    
    # Django call the __len__ method for every related model when using
    # select_related...
#    def __len__(self):
#        return len(self._descriptors)
    
    def items(self):
        return self._descriptors
    
    def __hash__(self):
        return self.original.__hash__()
    
    @property
    def max_weight(self):
        if self._max_weight is None: # Thread cache
            try:
                #Ordered by -weight by default
                self._max_weight = self.triggertodescriptor_set.all().only('weight')[0].weight
            except TriggerToDescriptor.DoesNotExist:
                # Should not occur.
                self._max_weight = 0
        return self._max_weight
#        return max(self[d.descriptor].weight for d in self)
    
#    def init_descriptors(self, **kwargs):
#        """
#        Take a text descriptors storage and create the links.
#        """
#        #original may be the full orginal line
#        if "original" in kwargs:
#            for d in kwargs["original"].split("\t")[1:]:#TODO check errors
#                ds = d.split()
#                original = ds[:-1]
#                dsc, created = Descriptor.get_or_create(original, self.parent, original=original)
#                self.connect(dsc, float(ds[-1]))
    
    def connect(self, descriptor, score):
        """
        Create a connection with the descriptor if doesn't yet exists.
        In each case, update the connection weight.
        Delete the connection if the score is negative.
        """
        if not descriptor in self:
#            sulci_logger.debug(u"Creating connection %s - %s" % (self, descriptor), "CYAN")
            self[descriptor] = 0.0
        rel = self[descriptor]
        rel.weight += score
        rel.save()
#        if self[descriptor] < 0:
#            del self[descriptor]
#            sulci_logger.debug(u"Removed connection %s - %s" % (self, descriptor), "RED")
    
    def clean_connections(self):
        """
        Remove the negative connections.
        """
        for descriptor in self._descriptors.copy().__iter__():
            if self[descriptor] < 0:
                del self[descriptor]
                sulci_logger.debug(u"Removed connection %s - %s" % (self, descriptor), "RED")        
    
    @classmethod
    def clean_all_connections(cls):
        TriggerToDescriptor.objects.filter(weight__lte=0).delete()
    
    def export(self):
        """
        Return a string for file storage.
        """
        if len(self) == 0:
            sulci_logger.debug(u"No descriptors for %s" % unicode(self), "RED")
            return None
        return u"%s\t%s" % (unicode(self), u"\t".join(u"%s %f" % (unicode(k), float(v)) for k, v in self.items()))
