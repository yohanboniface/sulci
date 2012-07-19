#!/usr/bin/env python
# -*- coding:Utf-8 -*-

from sulci.validators import KeyEntityValidator

from sulci_cli import SulciBaseCommand


class Command(SulciBaseCommand):
    """
    Sulci command for training the algoritms.
    """
    help = __doc__

    def define_args(self):
        super(Command, self).define_args()
        self.parser.add_argument(
            "-K",
            "--kev",
            action="store_true",
            dest="keyentities",
            help="Control the KeyEntity"
        )

    def handle(self, *args, **options):
        if self.KEYENTITIES:
            V = KeyEntityValidator()
            V.do()
        if self.IPDB:
            import ipdb
            ipdb.set_trace()

if __name__ == '__main__':
    command = Command()
    command.handle()
