# -*- coding:Utf-8 -*-
"""
Here is the modelization:

`Thesaurus`

    Its a wrapper to interact with the descriptors 

`Descriptor`

    This is a semantical entity, which will be used to describe the content.
    
    It has the fields:
    
    - name: the human readable name of the decriptor
    - description: some text to describe better the meaning of the descriptor
    - parent: a parent descriptor
    - is_alias_of: a parent of which the current descriptor is an alias

`Trigger`

    This is a piece of text that has been selected as having meaning.

"""
import re
import codecs
import os

from limpyd import model, fields

from sulci.textutils import tokenize_text, lev
from sulci.base import RetrievableObject
from sulci.utils import save_to_file, get_dir

class Thesaurus(object):

    def __init__(self, path="thesaurus.txt"):
        self.descriptors = Descriptor.collection()
    
    def __contains__(self, item):
        # TODO: accept also Desciptor instances as param
        return Descriptor.exists(name=item)
    
    def __iter__(self): 
        return Descriptor.instances()
    
    def __getitem__(self, key):
        return Descriptor.objects.get(name=unicode(key))
    
    def normalize_item(self, item):
        from textmining import KeyEntity  # Sucks...
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


class Descriptor(model.RedisModel): 
    """
    Entries of the Thesaurus.
    """
    
#    parent = model.ReferenceField('Descriptor')
    name = model.HashableField(unique=True)
    description = model.HashableField()
    count = model.HashableField(default=0)
    max_weight = model.HashableField(default=0)
#    is_alias_of = model.ReferenceField('Descriptor')
    
    def __init__(self, *args, **kwargs):
        self._max_weight = None
        super(Descriptor, self).__init__(*args, **kwargs)
    
    def __unicode__(self):
        return self.name.hget().decode('utf-8')

    def __str__(self):
        return self.name.hget()

    def __repr__(self):
        return "<Descriptor %s: %s>" % (self.pk.get(), self.name.hget())

    # @property
    # def max_weight(self):
    #     if self._max_weight is None: # Thread cache
    #         try:
    #             #Ordered by -weight by default
    #             self._max_weight = self.triggertodescriptor_set.all()[0].weight
    #         except TriggerToDescriptor.DoesNotExist:
    #             # Should not occur.
    #             self._max_weight = 0
    #     return self._max_weight
    
    @property
    def primeval(self):
        """
        Returns the primeval descriptor when self is alias of another.
        """
        if self.is_alias_of is None:
            return self
        return self.is_alias_of.primeval

#class TriggerToDescriptor(model.Model):
#    """
#    This is the "synapse" of the trigger to descriptor relation.
#    """
#    descriptor = model.ReferenceField(Descriptor)
#    trigger = model.ReferenceField("Trigger")
#    weight = model.FloatField(default=0)
#    
#    @property
#    def pondered_weight(self):
#        """
#        Give the weight of the relation, relative to the max weight of the
#        trigger and the max weight of the descriptor.
#        """
#        # current weigth relative to trigger max weight
#        weight = self.weight / self.trigger.max_weight
#        # current weight relative to descriptor max weight
#        weight *= self.weight / self.descriptor.max_weight
##        # current weight relative to trigger count
##        # we use logarithm to limit negative impact for very common triggers
##        weight *= math.log(self.weight) / math.log(self.trigger.count)
##        # current weight relative to descriptor occurrences in training
##        # Using log to limit impact
##        weight *= \
##           math.log(self.weight) / math.log(self.descriptor.trained_occurrences)
#        return weight
#    
#    class Meta:
#        unique_together = ("descriptor", "trigger")
#        ordering = ["-weight"]

#    def __unicode__(self):
#        return u"%s =[%f]=> %s" % (self.trigger, self.weight, self.descriptor)


class TriggerToDescriptor(model.RedisModel):
    """
    Helper to manage the trigger to descriptor relation.
    """
    trigger_id = model.HashableField(indexable=True)
    descriptor_id = model.HashableField(indexable=True)
    weight = model.HashableField(default=1)

    # def __init__(self, trigger, descriptor):
    #     """
    #     Trigger and descriptor could be instances, or pk.
    #     """
    #     super(TriggerToDescriptor, self).__init__(*args, **kwargs)
    #     self._trigger = None  # Used for caching the linked trigger instance
    #     self._descriptor = None  # idem for descriptor linked instance
    #     if isinstance(trigger, (int, str)):
    #         # shortcut to be able to pass the pk as parameter
    #         trigger_id = int(trigger)
    #     elif isinstance(trigger, Trigger):
    #         trigger_id = trigger.pk
    #         self._trigger = trigger  # Cache the instance
    #     else:
    #         raise ValueError("trigger param must be either a pk or a Trigger "
    #                          "instance, not %s" % type(trigger))
    #     if isinstance(descriptor, (int, str)):
    #         descriptor_id = int(trigger)
    #     elif isinstance(descriptor, Descriptor):
    #         descriptor_id = descriptor.pk
    #         self._descriptor = descriptor
    #     else:
    #         raise ValueError("descriptor param must be either a pk or a "
    #                          "Descriptor instance, not %s" % type(descriptor))

    @property
    def trigger(self):
        """
        Returns the trigger instance corresponding to the pk stored.
        """
        if not "_trigger" in dir(self) \
                            or self._trigger.pk.get() != self.trigger_id.hget():
            # Fetch or refetch it
            self._trigger = Trigger(self.trigger_id.hget())
        return self._trigger

    @property
    def descriptor(self):
        """
        Return the descriptor instance corresponding to the pk stored.
        """
        if not "_descriptor" in dir(self) \
                       or self._descriptor.pk.get() != self.descriptor_id.hget():
            # Fetch or refetch it
            self._descriptor = Descriptor(self.descriptor_id.hget())
        return self._descriptor

    def post_command(self, sender, name, result, args, kwargs):
        if (isinstance(sender, fields.RedisField)
            and sender.name == "weight" 
            and name in sender.available_modifiers
            and self.trigger_id.hget() is not None):  # Means instantiation is done
            if int(self.weight.hget()) > int(self.trigger.max_weight.hget()):
                self.trigger.max_weight.hset(self.weight.hget())
            if int(self.weight.hget()) > int(self.descriptor.max_weight.hget()):
                self.descriptor.max_weight.hset(self.weight.hget())
        return result

    @property
    def pondered_weight(self):
       """
       Give the weight of the relation, relative to the max weight of the
       trigger and the max weight of the descriptor.
       """
       # current weigth relative to trigger max weight
       weight = int(self.weight.hget()) / int(self.trigger.max_weight.hget())
       # current weight relative to descriptor max weight
       weight *= int(self.weight.hget()) / int(self.descriptor.max_weight.hget())
       return weight


class Trigger(model.RedisModel):
    """
    The trigger is a keyentity who suggest some descriptors when in a text.
    It is linked to one or more descriptors, and the distance of the link
    between the trigger and a descriptor is stored in the relation.
    This score is populated during the sementical training.
    """
    original = model.HashableField(unique=True)
    count = model.HashableField(default=0)
    max_weight = model.HashableField(default=0)

    def __init__(self, *args, **kwargs):
        self._max_weight = None
        # We cache relatins to descriptors. But during training, some other processes
        # could create and modify relations. This is a potential source of
        # bad behaviour, but at the moment I prefer to have good performance
        # cause I launch very often the script for testing it...
#        self._cached_descriptors = None
        self._cached_synapses = None
        super(Trigger, self).__init__(*args, **kwargs)
#        self.id = pk#Tuple of original string
#        self.original = u" ".join(pk)
#        self.parent = kwargs["parent"]
#        self._descriptors = {}
#        self.init_descriptors(**kwargs)
    
#    @property
#    def _descriptors(self):
#        if self._cached_descriptors is None:
#            self._cached_descriptors = list(self.descriptors.all())
#        return self._cached_descriptors

    @property
    def _synapses(self):
        if self._cached_synapses is None:
            self._cached_synapses = \
                        TriggerToDescriptor.collection(trigger_id=self.pk.get())[:20]
        return self._cached_synapses

    def __unicode__(self):
        return unicode(self.original.hget())

    def __contains__(self, key):
        if isinstance(key, Descriptor):
            return TriggerToDescriptor.exists(trigger_id=self.pk.get(), descriptor_id=key.pk.pk())
        elif isinstance(key, str):
            # FIXME: remove
            return key in self.original.hget()

    def __setitem__(self, key, value):
        if not isinstance(key, Descriptor):
            raise ValueError("Key must be Descriptor instance, got %s (%s) instead" 
                                                        % (str(key), type(key)))
        # Flush descriptors cache
        self._cached_descriptors = None
        t2d = TriggerToDescriptor(trigger_id=self.pk.get(), descriptor_id=key.pk.get())
        t2d.weight.hincrby(amount=value)
    
    def __getitem__(self, key):
        return TriggerToDescriptor.get(descriptor_id=key.pk.get(), trigger=self.pk.get())
    
#    def __delitem__(self, key):
#        return self._descriptors.__delitem__(key)
    
    def __iter__(self):
        return TriggerToDescriptor.instances(trigger_id=self.pk.get())

    # Django call the __len__ method for every related model when using
    # select_related...
#    def __len__(self):
#        return len(self._descriptors)
    
    def items(self):
        return self._descriptors
    
    # @property
    # def max_weight(self):
    #     if self._max_weight is None: # Thread cache
    #         try:
    #             max_descriptor_pk = self.descriptors.zrevrange(0, 1)[0]
    #         except IndexError:
    #             self._max_weight = 0
    #         else:
    #             self._max_weight = self.descriptors.zscore(max_descriptor_pk)
    #         # try:
    #         #     #Ordered by -weight by default
    #         #     self._max_weight = self.triggertodescriptor_set.all().only('weight')[0].weight
    #         # except TriggerToDescriptor.DoesNotExist:
    #         #     # Should not occur.
    #         #     self._max_weight = 0
    #     return self._max_weight
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
    
    def connect(self, descriptor, score=1):
        """
        Create a connection with the descriptor if doesn't yet exists.
        In each case, update the connection weight.
        Delete the connection if the score is negative.
        """
#        if not descriptor in self:
##            sulci_logger.debug(u"Creating connection %s - %s" % (self, descriptor), "CYAN")
#            self[descriptor] = 0.0
        self[descriptor] = score
#        rel.weight += score
#        rel.save()
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
