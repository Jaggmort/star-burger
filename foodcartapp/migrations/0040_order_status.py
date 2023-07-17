# Generated by Django 3.2.15 on 2023-06-28 21:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0039_auto_20230617_2333'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[('created', 'Создан'), ('cooking', 'Готовится'), ('delivering', 'Доставляется'), ('completed', 'Выполнен')], db_index=True, default='created', max_length=20, verbose_name='Статус заказа'),
        ),
    ]
