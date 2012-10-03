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
import codecs

from limpyd import fields

from sulci.base import BaseRedisModel
from sulci.utils import save_to_file, get_dir
from sulci.log import sulci_logger


class Thesaurus(object):

    def __init__(self, path="thesaurus.txt"):
        self.descriptors = Descriptor.collection()

    def __contains__(self, item):
        # TODO: accept also Descriptor instances as param
        return Descriptor.exists(name=item)

    def __iter__(self):
        return Descriptor.instances()

    def __getitem__(self, key):
        return Descriptor.get(name=unicode(key))

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
        if self._triggers is None:  # cached and lazy
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


class Descriptor(BaseRedisModel):
    """
    Entries of the Thesaurus.
    """

#    parent = model.ReferenceField('Descriptor')
    name = fields.HashableField(unique=True)
    description = fields.HashableField()
    count = fields.HashableField(default=0)
    max_weight = fields.HashableField(default=0)
    is_alias_of_id = fields.HashableField()

    def __init__(self, *args, **kwargs):
        self._max_weight = None
        super(Descriptor, self).__init__(*args, **kwargs)

    def __unicode__(self):
        return self.name.hget().decode('utf-8')

    def __str__(self):
        return self.name.hget()

    def __repr__(self):
        return "<Descriptor %s: %s>" % (self.pk.get(), self.name.hget())

    @property
    def primeval(self):
        """
        Returns the primeval descriptor when self is alias of another.
        """
        if not self.is_alias_of_id.hget():
            return self
        primeval = Descriptor(self.is_alias_of_id.hget())
        return primeval.primeval

    def remove_useless_connections(self, min=0.01):
        """
        Delete all the useless connections.

        First loop on all the descriptors to consume less RAM.
        """
        instances = TriggerToDescriptor.instances(descriptor_id=self.pk.get())
        for inst in instances:
            weight = inst.pondered_weight
            if weight < min:
                sulci_logger.info("Removing TriggerToDescriptor %s, between Trigger %s and Descriptor %s (weight: %f)" % (inst.pk.get(), inst.trigger_id.hget(), inst.descriptor_id.hget(), weight))
                inst.delete()

    @property
    def synapses(self):
        return TriggerToDescriptor.collection(descriptor_id=self.pk.get()).sort(by='-weight')


class TriggerToDescriptor(BaseRedisModel):
    """
    Helper to manage the trigger to descriptor relation.
    """
    pk = fields.PKField()
    trigger_id = fields.HashableField(indexable=True)
    descriptor_id = fields.HashableField(indexable=True)
    weight = fields.HashableField(default=1)

    def __repr__(self):
        return "<TriggerToDescriptor %s>" % self.__str__()

    def __unicode__(self):
        return "%s=[%s]>%s" % (
            unicode(self.trigger),
            self.weight.hget(),
            unicode(self.descriptor)
        )

    def __str__(self):
        return "%s=[%s]>%s" % (
            str(self.trigger),
            self.weight.hget(),
            str(self.descriptor)
        )

    @property
    def trigger(self):
        """
        Returns the trigger instance corresponding to the pk stored.
        """
        if not hasattr(self, "_trigger") \
                            or self._trigger.pk.get() != self.trigger_id.hget():
            # Fetch or refetch it
            self._trigger = Trigger(self.trigger_id.hget())
        return self._trigger

    @property
    def descriptor(self):
        """
        Return the descriptor instance corresponding to the pk stored.
        """
        if not hasattr(self, "_descriptor") \
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
        weight = float(self.weight.hget()) / float(self.trigger.max_weight.hget())
        # current weight relative to descriptor max weight
        weight *= float(self.weight.hget()) / float(self.descriptor.max_weight.hget())
        return weight

    @classmethod
    def get_or_connect(cls, trigger_id, descriptor_id):
        """
        Get instances by pk to prevent from creating several times the same relation.
        """
        pk = "%s|%s" % (trigger_id, descriptor_id)
        inst, created = super(cls, TriggerToDescriptor).get_or_connect(pk=pk)
        if created:
            # update the fields
            inst.trigger_id.hset(trigger_id)
            inst.descriptor_id.hset(descriptor_id)
        return inst, created

    @classmethod
    def remove_unique_connections(cls):
        """
        Delete all the connections which occurred one during training.

        First loop on all the descriptors to consume less RAM.
        """
        for descriptor_id in Descriptor.collection():
            instances = cls.instances(descriptor_id=descriptor_id)
            for inst in instances:
                try:
                    weight = int(inst.weight.hget())
                except TypeError:
                    sulci_logger.info("Removing TriggerToDescriptor %s without weight, between Trigger %s and Descriptor %s" % (inst.pk.get(), inst.trigger_id.hget(), inst.descriptor_id.hget()), "RED")
                    inst.delete()
                    continue
                if weight <= 1:
                    sulci_logger.info("Removing TriggerToDescriptor %s, between Trigger %s and Descriptor %s" % (inst.pk.get(), inst.trigger_id.hget(), inst.descriptor_id.hget()))
                    inst.delete()

    @classmethod
    def remove_useless_connections(cls, min=0.01):
        """
        Remove all the connections where pondered_weight is lower than
        `min` (by default 0.01)
        """
        for descriptor in Descriptor.instances().sort():
            descriptor.remove_useless_connections(min)


class Trigger(BaseRedisModel):
    """
    The trigger is a keyentity who suggest some descriptors when in a text.
    It is linked to one or more descriptors, and the distance of the link
    between the trigger and a descriptor is stored in the relation.
    This score is populated during the sementical training.
    """
    original = fields.HashableField(unique=True)
    count = fields.HashableField(default=0)
    max_weight = fields.HashableField(default=0)

    def __init__(self, *args, **kwargs):
        self._max_weight = None
        self._cached_synapses = None
        super(Trigger, self).__init__(*args, **kwargs)

    @property
    def _synapses(self):
        if self._cached_synapses is None:
            self._cached_synapses = \
                        TriggerToDescriptor.instances(trigger_id=self.pk.get()).sort(by="-weight")[:20]
        return self._cached_synapses

    def __unicode__(self):
        return self.original.hget().decode('utf-8')

    def __str__(self):
        return self.original.hget()

    def __repr__(self):
        return "<Trigger %s: %s>" % (self.pk.get(), self.original.hget())

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
        t2d, _ = TriggerToDescriptor.get_or_connect(trigger_id=self.pk.get(), descriptor_id=key.pk.get())
        t2d.weight.hincrby(amount=value)

    def __getitem__(self, key):
        return TriggerToDescriptor.get(descriptor_id=key.pk.get(), trigger=self.pk.get())

    def __iter__(self):
        return self._synapses.__iter__()

    def connect(self, descriptor, score=1):
        """
        Create a connection with the descriptor if doesn't yet exists.
        In each case, update the connection weight.
        Delete the connection if the score is negative.
        """
        self[descriptor] = score

    @classmethod
    def remove_orphans(cls):
        """
        After cleaning connections, some trigger could remain
        without any connection. So delete it.
        """
        for trigger in cls.instances().sort():
            if len(trigger._synapses) == 0:
                sulci_logger.info(u"Removing trigger %s" % trigger)
                trigger.delete()
