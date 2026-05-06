from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('marketplace', '0024_merge_20260505_1509'),
    ]

    operations = [
        migrations.RunSQL(
            sql='ALTER TABLE marketplace_customerorder DROP COLUMN IF EXISTS special_instructions;',
            reverse_sql='ALTER TABLE marketplace_customerorder ADD COLUMN special_instructions TEXT NOT NULL DEFAULT \'\';',
        ),
    ]
