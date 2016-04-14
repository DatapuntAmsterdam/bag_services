from django.core.management import BaseCommand
from django.db import connection
from django.db import ProgrammingError


class Command(BaseCommand):
    def handle(self, *args, **options):
        cursor = connection.cursor()
        tables = connection.introspection.get_table_list(cursor)

        for table_info in tables:
            if table_info.type == 'v' and table_info.name[0:4] == 'geo_':
                try:
                    cursor.execute('DROP MATERIALIZED VIEW {}_mat'.format(table_info.name))
                    self.stdout.write('removed {}_mat'.format(table_info.name))
                except ProgrammingError:
                    pass
