# -*- coding:Utf-8 -*-
"""
This module provide some facilities who can be used outside sulci.
"""

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
    origin_count = origin.triggertodescriptor_set.count()
    destination_count = destination.triggertodescriptor_set.count()
    if origin_count > destination_count and not force:
        raise ValueError("Origin has more relations than destination, use force.")
    # We loop over the origin relations
    for relation in origin.triggertodescriptor_set.all():
        sulci_logger.info(u"Handle relation %s" % unicode(relation))
        trigger = relation.trigger
        score = relation.weight
        # We create or update the relation from the trigger to the destination
        # descriptor
        trigger.connect(destination, score)
        # Delete the original relation
        relation.delete()
    
    # Make origin an alias of destination
    origin.is_alias_of = destination
    origin.save()
