# wildberries/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Store(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, verbose_name='Название магазина в нашей системе')
    wildberries_name = models.CharField(max_length=255, verbose_name='Название магазина в системе Wildberries', blank=True)
    wildberries_api_key = models.CharField(max_length=512, verbose_name='API ключ Wildberries')  # Увеличили размер поля
    STATUS_CHOICES = (
        ('active', 'Активный'),
        ('inactive', 'Неактивный'),
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='inactive', verbose_name='Статус')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания в нашей системе')

    def update_campaigns(self):
        from .tasks import fetch_and_save_campaigns
        fetch_and_save_campaigns.delay(self.id)

    def __str__(self):
        return self.name


class Campaign(models.Model):

    STATUS_CHOICES = {
        -1: "Кампания в процессе удаления",
        4: "Готова к запуску",
        7: "Кампания завершена",
        8: "Отказался",
        9: "Идут показы",
        11: "Кампания на паузе"
    }

    TYPE_CHOICES = {
        4: "кампания в каталоге",
        5: "кампания в карточке товара",
        6: "кампания в поиске",
        7: "кампания в рекомендациях на главной странице",
        8: "автоматическая кампания",
        9: "поиск + каталог"
    }

    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, verbose_name='Название кампании')
    start_time = models.DateTimeField(verbose_name='Время начала')
    end_time = models.DateTimeField(verbose_name='Время окончания')
    create_time = models.DateTimeField(verbose_name='Время создания')
    change_time = models.DateTimeField(verbose_name='Время изменения')
    search_pluse_state = models.BooleanField(default=False, verbose_name='Состояние поиска Plus')
    daily_budget = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Дневной бюджет')
    advert_id = models.BigIntegerField(verbose_name='ID рекламы')
    status = models.IntegerField(verbose_name='Статус')
    type = models.IntegerField(verbose_name='Тип')
    payment_type = models.CharField(max_length=10, verbose_name='Тип оплаты')

    def get_status_display(self):
        return self.STATUS_CHOICES.get(self.status, "Неизвестный статус")

    def get_type_display(self):
        return self.TYPE_CHOICES.get(self.type, "Неизвестный тип")

    def is_active(self):
        return self.status is 9

    def __str__(self):
        return self.name


class Subject(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255, verbose_name='Название предмета')

    def __str__(self):
        return self.name


class Set(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255, verbose_name='Название сета')

    def __str__(self):
        return self.name


class Menu(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255, verbose_name='Название меню')

    def __str__(self):
        return self.name


class UnitedParam(models.Model):
    campaign = models.ForeignKey(Campaign, related_name='united_params', on_delete=models.CASCADE)
    catalog_cpm = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Catalog CPM')
    search_cpm = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Search CPM')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    menus = models.ManyToManyField(Menu)
    sets = models.ManyToManyField(Set)
    nms = models.JSONField(verbose_name='NMS', default=list)
    nmCPMs = models.JSONField(verbose_name='nmCPM', default=list)
    active_carousel = models.BooleanField(default=False, verbose_name='Active Carousel')
    active_recom = models.BooleanField(default=False, verbose_name='Active Recom')
    active_booster = models.BooleanField(default=False, verbose_name='Active Booster')

    def __str__(self):
        return f'{self.campaign.name} - {self.subject.name}'


class CampaignStatistic(models.Model):
    campaign = models.ForeignKey(Campaign, related_name='statistics', on_delete=models.CASCADE)
    date = models.DateField()
    views = models.IntegerField()
    clicks = models.IntegerField()
    ctr = models.FloatField()
    cpc = models.DecimalField(max_digits=10, decimal_places=2)
    sum = models.DecimalField(max_digits=10, decimal_places=2)
    atbs = models.IntegerField()
    orders = models.IntegerField()
    cr = models.FloatField()
    shks = models.IntegerField()
    sum_price = models.DecimalField(max_digits=10, decimal_places=2)

class PlatformStatistic(models.Model):

    TYPE_CHOICES = {
        1: "Сайт",
        32: "Android",
        64: "iOs"
    }
    campaign_statistic = models.ForeignKey(CampaignStatistic, related_name='platforms', on_delete=models.CASCADE)
    app_type = models.IntegerField()
    views = models.IntegerField()
    clicks = models.IntegerField()
    ctr = models.FloatField()
    cpc = models.DecimalField(max_digits=10, decimal_places=2)
    sum = models.DecimalField(max_digits=10, decimal_places=2)
    atbs = models.IntegerField()
    orders = models.IntegerField()
    cr = models.FloatField()
    shks = models.IntegerField()
    sum_price = models.DecimalField(max_digits=10, decimal_places=2)

    def platform_type_display(self):
        return self.TYPE_CHOICES.get(self.app_type, "Неизвестный тип")

class ProductStatistic(models.Model):
    platform_statistic = models.ForeignKey(PlatformStatistic, related_name='products', on_delete=models.CASCADE)
    nm_id = models.BigIntegerField()
    name = models.CharField(max_length=255)
    views = models.IntegerField()
    clicks = models.IntegerField()
    ctr = models.FloatField()
    cpc = models.DecimalField(max_digits=10, decimal_places=2)
    sum = models.DecimalField(max_digits=10, decimal_places=2)
    atbs = models.IntegerField()
    orders = models.IntegerField()
    cr = models.FloatField()
    shks = models.IntegerField()
    sum_price = models.DecimalField(max_digits=10, decimal_places=2)


class CampaignKeywordStatistic(models.Model):
    campaign = models.ForeignKey(Campaign, related_name='keyword_statistics', on_delete=models.CASCADE)
    keyword = models.CharField(max_length=255)
    count = models.IntegerField()
    date_received = models.DateTimeField(default=timezone.now)

class KeywordData(models.Model):
    campaign = models.ForeignKey(Campaign, related_name='keyword_data', on_delete=models.CASCADE)
    phrase = models.JSONField()
    strong = models.JSONField()
    excluded = models.JSONField()
    pluse = models.JSONField()
    fixed = models.BooleanField()


class AutoCampaignKeywordStatistic(models.Model):
    campaign = models.ForeignKey(Campaign, related_name='auto_keyword_statistics', on_delete=models.CASCADE)
    keyword = models.CharField(max_length=255)
    views = models.IntegerField()
    clicks = models.IntegerField()
    ctr = models.FloatField()
    sum = models.FloatField()
    date_recorded = models.DateTimeField()

    class Meta:
        unique_together = ('campaign', 'keyword', 'date_recorded')