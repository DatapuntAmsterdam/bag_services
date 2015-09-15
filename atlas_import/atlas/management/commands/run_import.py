from django.core.management import BaseCommand

import datasets.bag.batch
import datasets.akr.batch
import datasets.lki.batch
import datasets.wkpb.batch
from batch import batch


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--no-bag',
                            action='store_false',
                            dest='run-bag',
                            default=True,
                            help='Skip BAG import')
        parser.add_argument('--no-kadaster',
                            action='store_false',
                            dest='run-kadaster',
                            default=True,
                            help='Skip kadaster import')
        parser.add_argument('--no-wkpb',
                            action='store_false',
                            dest='run-wkpb',
                            default=True,
                            help='Skip WKPB import')
        parser.add_argument('--no-index',
                            action='store_false',
                            dest='run-index',
                            default=True,
                            help='Skip elastic search indexing')

    def handle(self, *args, **options):
        if options['run-bag']:
            batch.execute(datasets.bag.batch.ImportBagJob())

        if options['run-kadaster']:
            batch.execute(datasets.akr.batch.ImportKadasterJob())
            batch.execute(datasets.lki.batch.ImportKadasterJob())

        if options['run-wkpb']:
            batch.execute(datasets.wkpb.batch.ImportWkpbJob())

        if options['run-index']:
            batch.execute(datasets.bag.batch.IndexJob())
