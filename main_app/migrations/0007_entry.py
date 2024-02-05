# Generated by Django 5.0.1 on 2024-02-05 23:00

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0006_alter_comment_created_at_alter_comment_journal'),
    ]

    operations = [
        migrations.CreateModel(
            name='Entry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=50)),
                ('text', models.TextField()),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('journal', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='entry', to='main_app.journal')),
            ],
        ),
    ]
