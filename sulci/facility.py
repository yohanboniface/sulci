# -*- coding:Utf-8 -*-
"""
This module provide some facilities who can be used outside sulci.
"""

from sulci.thesaurus import Trigger, Descriptor, TriggerToDescriptor
from sulci.log import sulci_logger


def merge_descriptors(origin, destination, force=False):
    """
    Move all relations from a descriptor `origin` to another descriptor
    `destination`, and make `origin` an alias of `destination`.

    Takes all relations of a descriptor, add or create the weigth
    of these relations to the destination descriptor relations, and delete
    the origin descriptors relations.
    """
    if origin == destination:
        raise ValueError("Origin and destination can't be equal !")
    origin_count = len(origin.synapses)
    destination_count = len(destination.synapses)
    if origin_count > destination_count and not force:
        raise ValueError("Origin has more relations than destination, use force.")

    for relation in origin.synapses.instances():
        sulci_logger.info(u"Handle relation %s" % unicode(relation))
        trigger = relation.trigger
        score = relation.weight.hget()

        # We create or update the relation from the trigger to the destination
        # descriptor
        trigger.connect(destination, score)
        # Delete the original relation
        relation.delete()

    # Make origin an alias of destination
    origin.is_alias_of_id.hset(destination.pk.get())


def remove_synapse(trigger, descriptor):
    """
    Remove a relation between a trigger and a descriptor.

    Both the parameters could be instances or str.
    """
    if not isinstance(trigger, Trigger):
        if isinstance(trigger, str):
            try:
                trigger = Trigger.objects.get(original=trigger)
            except Trigger.DoesNotExist:
                print "No trigger has been found"
                return
        else:
            raise ValueError("trigger must be either a str or Trigger instance")
    if not isinstance(descriptor, Descriptor):
        if isinstance(descriptor, str):
            try:
                descriptor = Descriptor.objects.get(name=descriptor)
            except Descriptor.DoesNotExist:
                print "No descriptor has been found"
                return
        else:
            raise ValueError("descriptor must be either a str or Trigger instance")

    # Here we have both the instances, so we can do the job
    try:
        synapse = TriggerToDescriptor.objects.get(trigger=trigger, descriptor=descriptor)
    except TriggerToDescriptor.DoesNotExist:
        print "No synapse has been found between %s and %s" % (trigger, descriptor)
    else:
        print "Deleting synapse %s" % synapse
        synapse.delete()
