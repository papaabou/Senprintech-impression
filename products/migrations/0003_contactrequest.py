from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0002_productoption_productoptionchoice"),
    ]

    operations = [
        migrations.CreateModel(
            name="ContactRequest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120)),
                ("email", models.EmailField(max_length=254)),
                ("phone", models.CharField(blank=True, max_length=40)),
                ("project_type", models.CharField(max_length=40)),
                ("message", models.TextField()),
                ("email_sent", models.BooleanField(default=False)),
                ("email_error", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "verbose_name": "demande contact",
                "verbose_name_plural": "demandes contact",
                "ordering": ["-created_at"],
            },
        ),
    ]
