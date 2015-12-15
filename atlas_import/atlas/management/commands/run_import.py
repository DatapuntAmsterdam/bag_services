from django.core.management import BaseCommand

import datasets.bag.batch
import datasets.brk.batch
import datasets.akr.batch
import datasets.lki.batch
import datasets.wkpb.batch
from batch import batch


class Command(BaseCommand):
    ordered = ['bag', 'brk', 'kadaster', 'wkpb']

    imports = dict(
        bag=[datasets.bag.batch.ImportBagJob],
        brk=[datasets.brk.batch.ImportKadasterJob],
        kadaster=[
            datasets.akr.batch.ImportKadasterJob,
            datasets.lki.batch.ImportKadasterJob
        ],
        wkpb=[datasets.wkpb.batch.ImportWkpbJob],
    )

    indexes = dict(
        bag=[datasets.bag.batch.IndexJob],
        brk=[],
        kadaster=[datasets.akr.batch.IndexKadasterJob],
        wkpb=[],
    )

    def add_arguments(self, parser):
        parser.add_argument('dataset',
                            nargs='*',
                            default=self.ordered,
                            help="Dataset to import, choose from {}".format(', '.join(self.imports.keys())))

        parser.add_argument('--no-import',
                            action='store_false',
                            dest='run-import',
                            default=True,
                            help='Skip database importing')

        parser.add_argument('--no-index',
                            action='store_false',
                            dest='run-index',
                            default=True,
                            help='Skip elastic search indexing')

    def handle(self, *args, **options):
        dataset = options['dataset']

        for ds in dataset:
            if ds not in self.imports.keys():
                self.stderr.write("Unkown dataset: {}".format(ds))
                return

        sets = [ds for ds in self.ordered if ds in dataset]     # enforce order

        self.stdout.write("Importing {}".format(", ".join(sets)))

        for ds in sets:
            if options['run-import']:
                for job_class in self.imports[ds]:
                    batch.execute(job_class())

            if options['run-index']:
                for job_class in self.indexes[ds]:
                    batch.execute(job_class())

