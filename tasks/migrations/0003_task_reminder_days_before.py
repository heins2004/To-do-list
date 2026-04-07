from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tasks", "0002_alter_task_options_remove_task_status_task_completed_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="task",
            name="reminder_days_before",
            field=models.PositiveIntegerField(default=1),
        ),
    ]
