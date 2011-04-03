# -*- coding:Utf-8 -*-
"""
This module provide some facilities who can be used outside sulci.
"""

from sulci.log import sulci_logger

def merge_descriptors(origin, destination):
    """
    This facility take all relations of a descriptor, add or create the weigth
    of these relations to the destination descriptor relations, and delete
    the origin descriptors relations.
    """
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
