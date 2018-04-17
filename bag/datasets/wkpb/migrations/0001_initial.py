# Generated by Django 2.0.1 on 2018-04-17 11:13

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('bag', '0001_initial'),
        ('brk', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Beperking',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False)),
                ('date_modified', models.DateTimeField(auto_now=True)),
                ('inschrijfnummer', models.IntegerField()),
                ('datum_in_werking', models.DateField()),
                ('datum_einde', models.DateField(null=True)),
            ],
            options={
                'verbose_name': 'Beperking',
                'verbose_name_plural': 'Beperkingen',
            },
        ),
        migrations.CreateModel(
            name='Beperkingcode',
            fields=[
                ('code', models.CharField(max_length=4, primary_key=True, serialize=False)),
                ('omschrijving', models.CharField(max_length=150, null=True)),
                ('date_modified', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Beperkingcode',
                'verbose_name_plural': 'Beperkingcodes',
            },
        ),
        migrations.CreateModel(
            name='BeperkingKadastraalObject',
            fields=[
                ('id', models.CharField(max_length=33, primary_key=True, serialize=False)),
                ('date_modified', models.DateTimeField(auto_now=True)),
                ('beperking', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='wkpb.Beperking')),
                ('kadastraal_object', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='brk.KadastraalObject')),
            ],
        ),
        migrations.CreateModel(
            name='BeperkingVerblijfsobject',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('beperking', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='wkpb.Beperking')),
                ('verblijfsobject', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bag.Verblijfsobject')),
            ],
        ),
        migrations.CreateModel(
            name='Broncode',
            fields=[
                ('code', models.CharField(max_length=4, primary_key=True, serialize=False)),
                ('omschrijving', models.CharField(max_length=150, null=True)),
                ('date_modified', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Broncode',
                'verbose_name_plural': 'Broncodes',
            },
        ),
        migrations.CreateModel(
            name='Brondocument',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False)),
                ('date_modified', models.DateTimeField(auto_now=True)),
                ('inschrijfnummer', models.IntegerField()),
                ('documentnaam', models.CharField(max_length=21)),
                ('persoonsgegevens_afschermen', models.NullBooleanField()),
                ('soort_besluit', models.CharField(max_length=60, null=True)),
                ('beperking', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='documenten', to='wkpb.Beperking')),
                ('bron', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='documenten', to='wkpb.Broncode')),
            ],
            options={
                'verbose_name': 'Brondocument',
                'verbose_name_plural': 'Brondocumenten',
            },
        ),
        migrations.AddField(
            model_name='beperking',
            name='beperkingtype',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='wkpb.Beperkingcode'),
        ),
        migrations.AddField(
            model_name='beperking',
            name='kadastrale_objecten',
            field=models.ManyToManyField(related_name='beperkingen', through='wkpb.BeperkingKadastraalObject', to='brk.KadastraalObject'),
        ),
        migrations.AddField(
            model_name='beperking',
            name='verblijfsobjecten',
            field=models.ManyToManyField(related_name='beperkingen', through='wkpb.BeperkingVerblijfsobject', to='bag.Verblijfsobject'),
        ),
    ]
