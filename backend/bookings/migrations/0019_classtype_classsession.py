from django.db import migrations, models
import django.core.validators
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("tenants", "0004_tenantsettings_business_type"),
        ("bookings", "0018_table_servicewindow"),
    ]

    operations = [
        migrations.CreateModel(
            name="ClassType",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=200)),
                ("description", models.TextField(blank=True, default="")),
                ("category", models.CharField(blank=True, default="", help_text="e.g. Cardio, Strength, Mind & Body", max_length=100)),
                ("duration_minutes", models.IntegerField(default=45, validators=[django.core.validators.MinValueValidator(5)])),
                (
                    "difficulty",
                    models.CharField(
                        choices=[
                            ("beginner", "Beginner"),
                            ("intermediate", "Intermediate"),
                            ("advanced", "Advanced"),
                            ("all", "All Levels"),
                        ],
                        default="all",
                        max_length=20,
                    ),
                ),
                ("max_capacity", models.IntegerField(default=20, validators=[django.core.validators.MinValueValidator(1)])),
                ("colour", models.CharField(blank=True, default="", help_text="Hex colour for timetable display", max_length=7)),
                ("price_pence", models.IntegerField(default=0, help_text="Price per session in pence (0 = included in membership)")),
                ("active", models.BooleanField(default=True)),
                ("sort_order", models.IntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "tenant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="class_types",
                        to="tenants.tenantsettings",
                    ),
                ),
            ],
            options={
                "ordering": ["sort_order", "name"],
            },
        ),
        migrations.CreateModel(
            name="ClassSession",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "day_of_week",
                    models.IntegerField(
                        choices=[
                            (0, "Monday"), (1, "Tuesday"), (2, "Wednesday"),
                            (3, "Thursday"), (4, "Friday"), (5, "Saturday"), (6, "Sunday"),
                        ]
                    ),
                ),
                ("start_time", models.TimeField()),
                ("end_time", models.TimeField()),
                ("room", models.CharField(blank=True, default="", help_text="e.g. Studio 1, Main Hall", max_length=100)),
                ("override_capacity", models.IntegerField(blank=True, help_text="Override class_type.max_capacity for this session", null=True)),
                ("active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "class_type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="sessions",
                        to="bookings.classtype",
                    ),
                ),
                (
                    "instructor",
                    models.ForeignKey(
                        blank=True,
                        help_text="Assigned instructor",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="class_sessions",
                        to="bookings.staff",
                    ),
                ),
                (
                    "tenant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="class_sessions",
                        to="tenants.tenantsettings",
                    ),
                ),
            ],
            options={
                "ordering": ["day_of_week", "start_time"],
            },
        ),
    ]
