from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("habits", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="HabitSkip",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("date", models.DateField()),
                ("reason", models.CharField(blank=True, max_length=200)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("habit", models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="skips", to="habits.habit")),
            ],
            options={
                "ordering": ["-date"],
                "unique_together": {("habit", "date")},
            },
        ),
    ]
