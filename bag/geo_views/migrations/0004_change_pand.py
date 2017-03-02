# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-09-06 14:30
from __future__ import unicode_literals

from django.db import migrations

from geo_views import migrate


class Migration(migrations.Migration):

    dependencies = [
        ('geo_views', '0003_auto_20160412_1138'),
    ]

    operations = [
        migrate.ManageView(
            view_name='geo_bag_pand',
            sql="""
SELECT
  p.id                                      AS id,
  p.geometrie                               AS geometrie,
  p.landelijk_id                            AS display,
  'bag/pand'::TEXT                          AS type,
  site.domain || 'bag/pand/' || p.id || '/' AS uri
FROM
  bag_pand p
  ,
  django_site site
WHERE
  site.name = 'API Domain'
""",
        ),

    ]
