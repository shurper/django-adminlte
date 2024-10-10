# wildberries/models.py
from collections import defaultdict
from datetime import timedelta

from django.core.cache import cache
from django.db.models import JSONField, Sum, IntegerField, DecimalField, ExpressionWrapper, Case, When, Value, \
    FloatField, F
from django.db import models
from django.contrib.auth.models import User
from django.db.models.functions import Coalesce
from django.utils import timezone


class Store(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, verbose_name='Название магазина в нашей системе')
    wildberries_name = models.CharField(max_length=255, verbose_name='Название магазина в системе Wildberries',
                                        blank=True)
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

    def current_user_has_access(self, request):
        return self.user == request.user

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
        return self.status == 9

    def current_user_has_access(self, request):
        return self.store.user == request.user

    def get_cpms_for_chart(self, product_id, destination_id, start_date, end_date, time_interval, keyword):
        now = timezone.now()
        campaign_id = self.id

        # Group logs by the chosen time interval and calculate the desired metrics
        time_deltas = {
            '5m': timedelta(minutes=5),
            '15m': timedelta(minutes=15),
            '1h': timedelta(hours=1),
            '4h': timedelta(hours=4),
            '1d': timedelta(days=1),
            '1w': timedelta(weeks=1),
            '1M': timedelta(days=30),
        }
        time_delta = time_deltas.get(time_interval, timedelta(hours=1))

        labels = []
        datasets = defaultdict(lambda: {'label': '', 'data': []})

        # Extract logs only for the specified keyword
        logs = AutoBidderLog.objects.filter(
            timestamp__range=(start_date, end_date),
            destination=destination_id,
            product_id=product_id,
            campaign_id=campaign_id,
            keyword=keyword
        ).values('timestamp', 'advert_competitors', 'cpms')

        # Prepare a dict to store logs by intervals
        interval_logs = defaultdict(list)

        for log in logs:
            interval_start = (log['timestamp'] - start_date) // time_delta * time_delta + start_date
            interval_logs[interval_start].append(log)

        current_time = start_date

        while current_time <= end_date:
            next_time = current_time + time_delta
            labels.append(current_time.isoformat())  # Using ISO format for timestamps

            if current_time <= now:
                cache_key = f'{campaign_id}_{destination_id}_{product_id}_{current_time}_{next_time}_{keyword}'
                if current_time != now:
                    interval_data = cache.get(cache_key)
                else:
                    interval_data = None

                if interval_data is None:
                    interval_data = defaultdict(list)

                    for log in interval_logs[current_time]:
                        advert_competitors = log.get('advert_competitors', [])
                        cpms = log.get('cpms', [])

                        # Ensure the lengths of advert_competitors and cpms match
                        if len(advert_competitors) == len(cpms):
                            for idx, (competitor_id, cpm) in enumerate(zip(advert_competitors, cpms)):
                                label = f'{competitor_id}_{cpm}'
                                interval_data[label].append(idx + 1)  # Position in the list (starting from 1)

                    cache.set(cache_key, interval_data, timeout=60)  # Cache for 1 minute

                for label, positions in interval_data.items():
                    datasets[label]['label'] = label
                    datasets[label]['data'].append(positions[0] if positions else None)
            else:
                for dataset in datasets.values():
                    dataset['data'].append(None)

            current_time = next_time

        return {
            'labels': labels,
            'datasets': [list(datasets.values())]
        }

    # def get_product_positions_for_chart(self, product_id, destination_id, start_date, end_date, time_interval):
    #     now = timezone.now()
    #     campaign_id = self.id
    #     # Group logs by the chosen time interval and calculate average position
    #     time_deltas = {
    #         '5m': timedelta(minutes=5),
    #         '15m': timedelta(minutes=15),
    #         '1h': timedelta(hours=1),
    #         '4h': timedelta(hours=4),
    #         '1d': timedelta(days=1),
    #         '1w': timedelta(weeks=1),
    #         '1M': timedelta(days=30),
    #     }
    #     time_delta = time_deltas.get(time_interval, timedelta(hours=1))
    #
    #     labels = []
    #     datasets = defaultdict(lambda: {'label': '', 'data': []})
    #
    #     # Extract all logs at once and process in memory
    #     logs = AutoBidderLog.objects.filter(
    #         timestamp__range=(start_date, end_date),
    #         destination=destination_id,
    #         product_id=product_id,
    #         campaign_id=campaign_id
    #     ).values('timestamp', 'keyword', 'position')
    #
    #     # Prepare a dict to store logs by intervals
    #     interval_logs = defaultdict(list)
    #
    #     for log in logs:
    #         interval_start = (log['timestamp'] - start_date) // time_delta * time_delta + start_date
    #         interval_logs[interval_start].append(log)
    #
    #     keywords = set(log['keyword'] for log in logs)
    #     current_time = start_date
    #
    #     while current_time <= end_date:
    #         next_time = current_time + time_delta
    #         labels.append(current_time.isoformat())  # Изменение формата временных меток
    #
    #         if current_time <= now:
    #             cache_key = f'{campaign_id}_{destination_id}_{product_id}_{current_time}_{next_time}'
    #             if current_time != now:
    #                 interval_data = cache.get(cache_key)
    #             else:
    #                 interval_data = None
    #
    #             if interval_data is None:
    #                 interval_data = defaultdict(list)
    #
    #                 for log in interval_logs[current_time]:
    #                     if log['position'] <= 200:
    #                         interval_data[log['keyword']].append(log['position'])
    #
    #                 for keyword, positions in interval_data.items():
    #                     avg_position = sum(positions) / len(positions) if positions else []
    #                     interval_data[keyword] = avg_position
    #
    #                 cache.set(cache_key, interval_data, timeout=60)  # Cache for
    #
    #             for keyword in keywords:
    #                 avg_position = interval_data.get(keyword, None)
    #                 datasets[keyword]['label'] = keyword
    #                 datasets[keyword]['data'].append(avg_position)
    #         else:
    #             for keyword in keywords:
    #                 datasets[keyword]['data'].append(None)
    #
    #         current_time = next_time
    #
    #     return {
    #         'labels': labels,
    #         'datasets': [list(datasets.values())]
    #     }

    # def get_product_positions_for_chart(self, product_id, destination_id, start_date, end_date, time_interval):
    #     now = timezone.now()
    #     campaign_id = self.id
    #
    #     # Group logs by the chosen time interval and calculate average position
    #     time_deltas = {
    #         '5m': timedelta(minutes=5),
    #         '15m': timedelta(minutes=15),
    #         '1h': timedelta(hours=1),
    #         '4h': timedelta(hours=4),
    #         '1d': timedelta(days=1),
    #         '1w': timedelta(weeks=1),
    #         '1M': timedelta(days=30),
    #     }
    #     time_delta = time_deltas.get(time_interval, timedelta(hours=1))
    #
    #     labels = []
    #     datasets = defaultdict(lambda: {'label': '', 'data': []})
    #     datasets_advert_position = defaultdict(lambda: {'label': 'Advert Position', 'data': []})
    #     datasets_advert_competitors_count = defaultdict(lambda: {'label': 'Advert Competitors Count', 'data': []})
    #     datasets_product_price = defaultdict(lambda: {'label': 'Product Price', 'data': []})
    #     datasets_cpm = defaultdict(lambda: {'label': 'CPM', 'data': []})
    #
    #     # Extract all logs at once and process in memory
    #     logs = AutoBidderLog.objects.filter(
    #         timestamp__range=(start_date, end_date),
    #         destination=destination_id,
    #         product_id=product_id,
    #         campaign_id=campaign_id
    #     ).values('timestamp', 'keyword', 'position', 'advert_position', 'advert_competitors_count', 'product_price',
    #              'cpm', 'advert_competitors')
    #
    #     # Prepare a dict to store logs by intervals
    #     interval_logs = defaultdict(list)
    #
    #     for log in logs:
    #         interval_start = (log['timestamp'] - start_date) // time_delta * time_delta + start_date
    #         interval_logs[interval_start].append(log)
    #
    #     keywords = set(log['keyword'] for log in logs)
    #     current_time = start_date
    #
    #     while current_time <= end_date:
    #         next_time = current_time + time_delta
    #         labels.append(current_time.isoformat())
    #
    #         if current_time <= now:
    #             cache_key = f'{campaign_id}_{destination_id}_{product_id}_{current_time}_{next_time}'
    #             if current_time != now:
    #                 interval_data = cache.get(cache_key)
    #             else:
    #                 interval_data = None
    #
    #             if interval_data is None:
    #                 interval_data = defaultdict(list)
    #
    #                 for log in interval_logs[current_time]:
    #                     if log['position'] <= 200:
    #                         # Основная позиция товара
    #                         interval_data[log['keyword']].append(log['position'])
    #
    #                         # Позиция относительно конкурентов
    #                         datasets_advert_position[log['keyword']]['data'].append(log.get('advert_position'))
    #
    #                         # Количество конкурентов
    #                         datasets_advert_competitors_count[log['keyword']]['data'].append(
    #                             log.get('advert_competitors_count'))
    #
    #                         # Стоимость товара
    #                         datasets_product_price[log['keyword']]['data'].append(log.get('product_price'))
    #
    #                     # CPM, с учетом возможного отсутствия в log['cpm']
    #                     if log.get('cpm') is not None:
    #                         datasets_cpm[log['keyword']]['data'].append(log['cpm'])
    #                     else:
    #                         # Найти индекс товара в advert_competitors (если это список)
    #                         competitors = log.get('advert_competitors', [])
    #                         if isinstance(competitors, list) and product_id in competitors:
    #                             product_index = competitors.index(product_id)
    #                             # Проверка, является ли элемент списка словарем
    #                             competitor_data = competitors[product_index]
    #                             if isinstance(competitor_data, dict):
    #                                 cpm_value = competitor_data.get('cpm')
    #                                 datasets_cpm[log['keyword']]['data'].append(cpm_value if cpm_value is not None else None)
    #                             else:
    #                                 datasets_cpm[log['keyword']]['data'].append(None)
    #                         else:
    #                             datasets_cpm[log['keyword']]['data'].append(None)
    #
    #                 for keyword, positions in interval_data.items():
    #                     avg_position = sum(positions) / len(positions) if positions else None
    #                     interval_data[keyword] = avg_position
    #
    #                 cache.set(cache_key, interval_data, timeout=60)  # Кэширование данных
    #
    #             for keyword in keywords:
    #                 avg_position = interval_data.get(keyword, None)
    #                 datasets[keyword]['label'] = keyword
    #                 datasets[keyword]['data'].append(avg_position)
    #         else:
    #             # Если текущее время больше, чем now, добавляем пустые значения
    #             for keyword in keywords:
    #                 datasets[keyword]['data'].append(None)
    #                 datasets_advert_position[keyword]['data'].append(None)
    #                 datasets_advert_competitors_count[keyword]['data'].append(None)
    #                 datasets_product_price[keyword]['data'].append(None)
    #                 datasets_cpm[keyword]['data'].append(None)
    #
    #         current_time = next_time
    #
    #     return {
    #         'labels': labels,
    #         'datasets': [
    #             list(datasets.values()),
    #             list(datasets_advert_position.values()),
    #             list(datasets_advert_competitors_count.values()),
    #             list(datasets_product_price.values()),
    #             list(datasets_cpm.values())
    #         ]
    #     }

    def get_product_positions_for_chart(self, product_id, destination_id, start_date, end_date, time_interval):
        now = timezone.now()
        campaign_id = self.id

        # Определение временных интервалов
        time_deltas = {
            '5m': timedelta(minutes=5),
            '15m': timedelta(minutes=15),
            '1h': timedelta(hours=1),
            '4h': timedelta(hours=4),
            '1d': timedelta(days=1),
            '1w': timedelta(weeks=1),
            '1M': timedelta(days=30),
        }
        time_delta = time_deltas.get(time_interval, timedelta(hours=1))

        labels = []
        datasets = defaultdict(lambda: {'label': '', 'data': []})
        datasets_advert_position = defaultdict(lambda: {'label': '', 'data': []})
        datasets_advert_competitors_count = defaultdict(lambda: {'label': '', 'data': []})
        datasets_product_price = defaultdict(lambda: {'label': '', 'data': []})
        datasets_cpm = defaultdict(lambda: {'label': '', 'data': []})

        # Получение всех логов за указанный период
        logs = AutoBidderLog.objects.filter(
            timestamp__range=(start_date, end_date),
            destination=destination_id,
            product_id=product_id,
            campaign_id=campaign_id
        ).values('timestamp', 'keyword', 'position', 'advert_position', 'advert_competitors_count', 'product_price',
                 'cpm', 'advert_competitors')

        # Подготовка логов, сгруппированных по интервалам
        interval_logs = defaultdict(list)
        for log in logs:
            interval_start = (log['timestamp'] - start_date) // time_delta * time_delta + start_date
            interval_logs[interval_start].append(log)

        keywords = set(log['keyword'] for log in logs)
        current_time = start_date

        while current_time <= end_date:
            next_time = current_time + time_delta
            labels.append(current_time.isoformat())  # Форматирование временных меток

            if current_time <= now:
                cache_key = f'{campaign_id}_{destination_id}_{product_id}_{current_time}_{next_time}'
                interval_data = cache.get(cache_key) if current_time != now else None

                if interval_data is None:
                    interval_data = {keyword: {'positions': [], 'advert_positions': [], 'competitors_counts': [],
                                               'prices': [], 'cpms': []} for keyword in keywords}

                    for log in interval_logs[current_time]:
                        keyword = log['keyword']
                        if log['position'] <= 200:
                            interval_data[keyword]['positions'].append(log['position'])

                        if 'advert_position' in log and 'advert_competitors_count' in log:
                            if log['advert_competitors_count'] > 0 and log['advert_position'] > 0:
                                strength = 1 - round(float(log['advert_position']) / log['advert_competitors_count'], 2)
                                interval_data[keyword]['advert_positions'].append(strength)
                            else:
                                interval_data[keyword]['advert_positions'].append(None)

                        if 'advert_competitors_count' in log:
                            interval_data[keyword]['competitors_counts'].append(log['advert_competitors_count'])
                        if 'product_price' in log:
                            interval_data[keyword]['prices'].append(log['product_price'])
                        if log.get('cpm') is not None:
                            interval_data[keyword]['cpms'].append(log['cpm'])
                        elif 'advert_competitors' in log:
                            try:
                                idx = log['advert_competitors'].index(product_id)
                                interval_data[keyword]['cpms'].append(log['advert_competitors'][idx]['cpm'])
                            except (ValueError, IndexError, KeyError):
                                pass

                    # Подсчет средних значений для каждого параметра
                    for keyword, data in interval_data.items():
                        # Подсчет количества ненулевых позиций
                        non_null_positions = [pos for pos in data['positions'] if pos is not None]
                        non_null_advert_positions = [pos for pos in data['advert_positions'] if pos is not None]
                        non_null_competitors_counts = [count for count in data['competitors_counts'] if
                                                       count is not None]
                        non_null_prices = [price for price in data['prices'] if price is not None]
                        non_null_cpms = [cpm for cpm in data['cpms'] if cpm is not None]

                        # Рассчитываем средние значения, если есть ненулевые элементы, иначе оставляем None
                        if non_null_positions:
                            data['avg_position'] = sum(non_null_positions) / len(non_null_positions)
                        else:
                            data['avg_position'] = None

                        if non_null_advert_positions:
                            data['avg_advert_position'] = sum(non_null_advert_positions) / len(
                                non_null_advert_positions)
                        else:
                            data['avg_advert_position'] = None

                        if non_null_competitors_counts:
                            data['avg_competitors_count'] = sum(non_null_competitors_counts) / len(
                                non_null_competitors_counts)
                        else:
                            data['avg_competitors_count'] = None

                        if non_null_prices:
                            data['avg_price'] = sum(non_null_prices) / len(
                                non_null_prices) / 100  # Переводим в нужный формат (цены)
                        else:
                            data['avg_price'] = None

                        if non_null_cpms:
                            data['avg_cpm'] = sum(non_null_cpms) / len(non_null_cpms)
                        else:
                            data['avg_cpm'] = None

                    cache.set(cache_key, interval_data, timeout=60)

                # Добавление данных в датасеты
                for keyword in keywords:
                    datasets.setdefault(keyword, {'label': '', 'data': []})
                    datasets_advert_position.setdefault(keyword, {'label': '', 'data': []})
                    datasets_advert_competitors_count.setdefault(keyword, {'label': '', 'data': []})
                    datasets_product_price.setdefault(keyword, {'label': '', 'data': []})
                    datasets_cpm.setdefault(keyword, {'label': '', 'data': []})

                    interval_keyword_data = interval_data.get(keyword, {})

                    datasets[keyword]['label'] = keyword
                    datasets[keyword]['data'].append(interval_keyword_data.get('avg_position'))

                    datasets_advert_position[keyword]['label'] = keyword
                    datasets_advert_position[keyword]['data'].append(interval_keyword_data.get('avg_advert_position'))

                    datasets_advert_competitors_count[keyword]['label'] = keyword
                    datasets_advert_competitors_count[keyword]['data'].append(
                        interval_keyword_data.get('avg_competitors_count'))

                    datasets_product_price[keyword]['label'] = keyword
                    datasets_product_price[keyword]['data'].append(interval_keyword_data.get('avg_price'))

                    datasets_cpm[keyword]['label'] = keyword
                    datasets_cpm[keyword]['data'].append(interval_keyword_data.get('avg_cpm'))


            else:
                # Добавление None для будущих интервалов
                for keyword in keywords:
                    datasets[keyword]['data'].append(None)
                    datasets_advert_position[keyword]['data'].append(None)
                    datasets_advert_competitors_count[keyword]['data'].append(None)
                    datasets_product_price[keyword]['data'].append(None)
                    datasets_cpm[keyword]['data'].append(None)

            current_time = next_time

        return {
            'labels': labels,
            'datasets': [
                list(datasets.values()),
                list(datasets_advert_position.values()),
                list(datasets_advert_competitors_count.values()),
                list(datasets_product_price.values()),
                list(datasets_cpm.values())
            ]
        }

    def get_stat_for_chart_by_product(self, product_id, start_date, end_date, time_interval):
        base_stats = (
            ProductStatistic.objects
            .filter(
                nm_id=product_id,
                platform_statistic__campaign_statistic__campaign=self,
                platform_statistic__campaign_statistic__date__range=(start_date, end_date)
            )
            .values('platform_statistic__campaign_statistic__date')
            .annotate(
                views=Coalesce(Sum('views'), 0, output_field=IntegerField()),
                clicks=Coalesce(Sum('clicks'), 0, output_field=IntegerField()),
                sum=Coalesce(Sum('sum'), 0, output_field=DecimalField()),
                atbs=Coalesce(Sum('atbs'), 0, output_field=IntegerField()),
                orders=Coalesce(Sum('orders'), 0, output_field=IntegerField()),
                actual_atbs=Coalesce(Sum('actual_atbs'), 0, output_field=IntegerField()),
                actual_orders=Coalesce(Sum('actual_orders'), 0, output_field=IntegerField()),
                cr=Coalesce(Sum('cr'), 0, output_field=DecimalField()),
                shks=Coalesce(Sum('shks'), 0, output_field=DecimalField()),
                sum_price=Coalesce(Sum('sum_price'), 0, output_field=DecimalField())
            )
            .annotate(
                ctr=ExpressionWrapper(
                    Case(
                        When(views__gt=0, then=F('clicks') * 100.0 / F('views')),
                        default=Value(0.0),
                        output_field=FloatField()
                    ),
                    output_field=FloatField()
                ),
                cpc=ExpressionWrapper(
                    Case(
                        When(clicks__gt=0, then=F('sum') * 1.0 / F('clicks')),
                        default=Value(0.0),
                        output_field=FloatField()
                    ),
                    output_field=FloatField()
                )
            )
            .order_by('platform_statistic__campaign_statistic__date')
        )

        time_deltas = {
            '5m': timedelta(minutes=5),
            '15m': timedelta(minutes=15),
            '1h': timedelta(hours=1),
            '4h': timedelta(hours=4),
            '1d': timedelta(days=1),
            '1w': timedelta(weeks=1),
            '1M': timedelta(days=30),
        }
        time_delta = time_deltas.get(time_interval, timedelta(hours=1))

        data = {
            'labels': [],
            'datasets': [
                {'label': 'Просмотры', 'data': [], 'borderColor': 'rgba(75, 192, 192, 1)', 'fill': False,
                 'hidden': True},
                {'label': 'Клики', 'data': [], 'borderColor': 'rgba(54, 162, 235, 1)', 'fill': False},
                {'label': 'CTR (кликабельность)', 'data': [], 'borderColor': 'rgba(255, 206, 86, 1)', 'fill': False},
                {'label': 'CPC (цена клика)', 'data': [], 'borderColor': 'rgba(75, 192, 192, 1)', 'fill': False},
                {'label': 'Затраты', 'data': [], 'borderColor': 'rgba(153, 102, 255, 1)', 'fill': False,
                 'hidden': True},
                {'label': 'Корзины', 'data': [], 'borderColor': 'rgba(255, 159, 64, 1)', 'fill': False},
                {'label': 'Заказы', 'data': [], 'borderColor': 'rgba(199, 199, 199, 1)', 'fill': False},
                {'label': 'Корзины из аналитики', 'data': [], 'borderColor': 'rgba(255, 99, 132, 1)', 'fill': False},
                {'label': 'Заказы из аналитики', 'data': [], 'borderColor': 'rgba(54, 162, 235, 1)', 'fill': False},
                {'label': 'CR (уровень конверсии - "заказы/клики")', 'data': [], 'borderColor': 'rgba(75, 192, 192, 1)',
                 'fill': False},
                {'label': 'Заказано товаров', 'data': [], 'borderColor': 'rgba(255, 206, 86, 1)', 'fill': False},
                {'label': 'Сумма заказов', 'data': [], 'borderColor': 'rgba(153, 102, 255, 1)', 'fill': False,
                 'hidden': True},
            ]
        }

        stats_by_interval = defaultdict(lambda: defaultdict(list))

        for stat in base_stats:
            interval_start = (stat[
                                  'platform_statistic__campaign_statistic__date'] - start_date) // time_delta * time_delta + start_date
            stats_by_interval[interval_start]['views'].append(stat['views'])
            stats_by_interval[interval_start]['clicks'].append(stat['clicks'])
            stats_by_interval[interval_start]['ctr'].append(stat['ctr'])
            stats_by_interval[interval_start]['cpc'].append(stat['cpc'])
            stats_by_interval[interval_start]['sum'].append(stat['sum'])
            stats_by_interval[interval_start]['atbs'].append(stat['atbs'])
            stats_by_interval[interval_start]['orders'].append(stat['orders'])
            stats_by_interval[interval_start]['actual_atbs'].append(stat['actual_atbs'])
            stats_by_interval[interval_start]['actual_orders'].append(stat['actual_orders'])
            stats_by_interval[interval_start]['cr'].append(stat['cr'])
            stats_by_interval[interval_start]['shks'].append(stat['shks'])
            stats_by_interval[interval_start]['sum_price'].append(stat['sum_price'])

        current_time = start_date
        while current_time <= end_date:
            next_time = current_time + time_delta

            interval_stats = stats_by_interval[current_time]

            if interval_stats:
                interval_data = {key: sum(values) / len(values) for key, values in interval_stats.items()}
            else:
                interval_data = {
                    'views': None,
                    'clicks': None,
                    'ctr': None,
                    'cpc': None,
                    'sum': None,
                    'atbs': None,
                    'orders': None,
                    'actual_atbs': None,
                    'actual_orders': None,
                    'cr': None,
                    'shks': None,
                    'sum_price': None,
                }

            # data['labels'].append(current_time.strftime('%d-%m-%Y %H:%M:%S'))
            data['labels'].append(current_time.isoformat())
            data['datasets'][0]['data'].append(interval_data['views'])
            data['datasets'][1]['data'].append(interval_data['clicks'])
            data['datasets'][2]['data'].append(interval_data['ctr'])
            data['datasets'][3]['data'].append(interval_data['cpc'])
            data['datasets'][4]['data'].append(interval_data['sum'])
            data['datasets'][5]['data'].append(interval_data['atbs'])
            data['datasets'][6]['data'].append(interval_data['orders'])
            data['datasets'][7]['data'].append(interval_data['actual_atbs'])
            data['datasets'][8]['data'].append(interval_data['actual_orders'])
            data['datasets'][9]['data'].append(interval_data['cr'])
            data['datasets'][10]['data'].append(interval_data['shks'])
            data['datasets'][11]['data'].append(interval_data['sum_price'])

            current_time = next_time

        return data

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

    def current_user_has_access(self, request):
        return self.campaign.store.user == request.user

    def __str__(self):
        return f'{self.campaign.name} - {self.subject.name}'


class CampaignStatistic(models.Model):
    campaign = models.ForeignKey(Campaign, related_name='statistics', on_delete=models.CASCADE)
    date = models.DateTimeField()
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

    def current_user_has_access(self, request):
        return self.campaign.store.user == request.user


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

    def current_user_has_access(self, request):
        return self.campaign_statistic.campaign.store.user == request.user

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
    actual_atbs = models.IntegerField(default=0)
    actual_orders = models.IntegerField(default=0)
    cr = models.FloatField()
    shks = models.IntegerField()
    sum_price = models.DecimalField(max_digits=10, decimal_places=2)

    def current_user_has_access(self, request):
        return self.platform_statistic.campaign_statistic.campaign.store.user == request.user


class CampaignKeywordStatistic(models.Model):
    campaign = models.ForeignKey(Campaign, related_name='keyword_statistics', on_delete=models.CASCADE)
    keyword = models.CharField(max_length=255)
    count = models.IntegerField()
    date_received = models.DateTimeField(default=timezone.now)

    def current_user_has_access(self, request):
        return self.campaign.store.user == request.user


class KeywordData(models.Model):
    campaign = models.ForeignKey(Campaign, related_name='keyword_data', on_delete=models.CASCADE)
    phrase = models.JSONField()
    strong = models.JSONField()
    excluded = models.JSONField()
    pluse = models.JSONField()
    additional = models.JSONField(verbose_name='additional', default=list)
    fixed = models.BooleanField()

    def current_user_has_access(self, request):
        return self.campaign.store.user == request.user

    @classmethod
    def get_fixed_keywords_choices(cls, campaign_id):
        keywords = cls.objects.filter(campaign_id=campaign_id).values_list('pluse', flat=True)
        flat_keywords = [item for sublist in keywords for item in sublist]
        return [(keyword, keyword) for keyword in flat_keywords]

    @classmethod
    def get_additional_keywords_choices(cls, campaign_id):
        keywords = cls.objects.filter(campaign_id=campaign_id).values_list('additional', flat=True)
        flat_keywords = [item for sublist in keywords for item in sublist]
        return [(keyword, keyword) for keyword in flat_keywords]


class AutoCampaignKeywordStatistic(models.Model):
    campaign = models.ForeignKey(Campaign, related_name='auto_keyword_statistics', on_delete=models.CASCADE)
    keyword = models.CharField(max_length=255)
    views = models.IntegerField()
    clicks = models.IntegerField()
    ctr = models.FloatField()
    sum = models.FloatField()
    date_recorded = models.DateTimeField()

    def current_user_has_access(self, request):
        return self.campaign.store.user == request.user

    class Meta:
        unique_together = ('campaign', 'keyword', 'date_recorded')


from django.db import models


class AutoBidderSettings(models.Model):
    campaign = models.OneToOneField(Campaign, on_delete=models.CASCADE)
    product_id = models.IntegerField(blank=True, null=True)
    depth = models.IntegerField(blank=True, null=True, default=1)
    destination = models.IntegerField(blank=True, null=True)
    keyword = models.CharField(max_length=255, blank=True, null=True)
    keywords_monitoring = models.JSONField(verbose_name='keywords_monitoring', default=list)
    keywords_monitoring_add = models.JSONField(verbose_name='keywords_monitoring_add', default=list)
    destinations_monitoring = models.JSONField(verbose_name='destinations_monitoring', default=list)
    max_bid = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    is_enabled = models.BooleanField(default=True)

    def current_user_has_access(self, request):
        return self.campaign.store.user == request.user

    def __str__(self):
        return f"AutoBidderSettings for campaign {self.campaign}"

    def get_monitoring_words(self):
        keywords_monitoring = self.keywords_monitoring or []
        keywords_monitoring_add = self.keywords_monitoring_add or []
        keyword = self.keyword.strip().lower() if isinstance(self.keyword, str) and self.keyword.strip() else None

        # Приводим слова к нижнему регистру, удаляем пустые строки и убираем дубли
        result = list(set(kw.lower().strip() for kw in keywords_monitoring + keywords_monitoring_add if
                          isinstance(kw, str) and kw.strip()))

        # Если keyword не пустая, добавляем её на первое место
        if keyword:
            result.insert(0, keyword)

        return result

    def save(self, *args, **kwargs):
        # Get the current instance before saving to compare
        try:
            current_instance = AutoBidderSettings.objects.get(pk=self.pk)
        except AutoBidderSettings.DoesNotExist:
            current_instance = None

        super().save(*args, **kwargs)

        if current_instance:
            if (
                    current_instance.keyword != self.keyword
                    or current_instance.keywords_monitoring != self.keywords_monitoring
                    or current_instance.keywords_monitoring_add != self.keywords_monitoring_add
                    or current_instance.destinations_monitoring != self.destinations_monitoring
            ):
                PositionTrackingTask.objects.filter(campaign=self.campaign).delete()


class PositionTrackingTask(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE)
    product_id = models.IntegerField()
    destination = models.IntegerField(null=True, blank=True)
    keyword = models.CharField(max_length=255)
    depth = models.IntegerField(blank=True, null=True, default=2)
    status = models.CharField(max_length=50,
                              choices=[('request', 'Request'), ('in_progress', 'In Progress'), ('done', 'Done')])
    actual_position = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    watcher_data = models.JSONField(verbose_name='watcher_data', default=list)  # Данные полученные от бота. Перезаписваются при каждом отчете от бота, но каждый раз сохраняются в AutobidderLog

    def current_user_has_access(self, request):
        return self.campaign.store.user == request.user


class PositionRange(models.Model):
    autobidder_settings = models.ForeignKey(AutoBidderSettings, on_delete=models.CASCADE,
                                            related_name='position_ranges')
    start_position = models.IntegerField()
    end_position = models.IntegerField()
    bid = models.DecimalField(max_digits=10, decimal_places=2)

    def current_user_has_access(self, request):
        return self.autobidder_settings.campaign.store.user == request.user

    def __str__(self):
        return f"{self.start_position}-{self.end_position}: {self.bid}"


class IntraDaySchedule(models.Model):
    autobidder_settings = models.ForeignKey(AutoBidderSettings, on_delete=models.CASCADE,
                                            related_name='intra_day_schedules')
    start_time = models.TimeField()
    end_time = models.TimeField()

    def current_user_has_access(self, request):
        return self.autobidder_settings.campaign.store.user == request.user

    def __str__(self):
        return f"{self.start_time} - {self.end_time}"


class WeeklySchedule(models.Model):
    autobidder_settings = models.ForeignKey(AutoBidderSettings, on_delete=models.CASCADE,
                                            related_name='weekly_schedules')
    day_of_week = models.CharField(max_length=20)

    def current_user_has_access(self, request):
        return self.autobidder_settings.campaign.store.user == request.user

    def __str__(self):
        return self.day_of_week


class AutoBidderLog(models.Model):
    """
    Модель для хранения логов работы автобиддера.

    Attributes:
        campaign (ForeignKey): Ссылка на рекламную кампанию.
        timestamp (DateTimeField): Время записи лога.
        message (TextField): Сообщение лога.
        keyword (TextField): Ключевая фраза мониторинга.
        depth (IntegerField): Глубина мониторинга - количество страниц для просмотра на ВБ.
        destination (IntegerField): Локация, из которой производится мониторинг.
        product_id (IntegerField): ID продукта, который мониторится.
        position (IntegerField): Позиция продукта в выдаче.
        clicks (IntegerField): Количество кликов по карточке продукта за текущую сессию.
        cards (IntegerField): Количество добавлений продукта в корзину за текущую сессию.
        orders (IntegerField): Количество заказов продукта за текущую сессию.
        position_delta (IntegerField): Изменение позиции продукта в результате продвижения.
        product_price (FloatField): Текущая цена продукта.
        average_cpm (FloatField): Средний CPM на первой странице ВБ.
        cpm (FloatField): Текущий CPM для рекламной кампании продукта.
        before_average_cpm (FloatField): Средний CPM у конкурентов перед продуктом.
        min_cpm (FloatField): Минимальный CPM на первой странице.
        before_min_cpm (FloatField): Минимальный CPM у конкурентов перед продуктом.
        max_cpm (FloatField): Максимальный CPM на первой странице.
        before_max_cpm (FloatField): Максимальный CPM у конкурентов перед продуктом.
        average_advert_step_cost (FloatField): Средняя стоимость продвижения на 1 позицию.
        before_average_advert_step_cost (FloatField): Средняя стоимость продвижения на 1 позицию у конкурентов перед продуктом.
        advert_density (FloatField): Коэффициент плотности рекламы на первой странице.
        advert_competitors_count (IntegerField): Количество рекламных конкурентов на первой странице.
        advert_competitors_before (IntegerField): Количество конкурентов перед продуктом.
        advert_competitors_after (IntegerField): Количество конкурентов после продукта.
        advert_position (IntegerField): Позиция продукта среди рекламных карточек.
        advert_count (IntegerField): Количество рекламных карточек на первой странице.
        cpms (JSONField): Список всех ставок CPM конкурентов.
        advert_step_costs (JSONField): Список стоимости продвижения на 1 позицию для конкурентов.
        advert_competitors (JSONField): Список ID конкурентов на первой странице.
        bid (FloatField): Текущая ставка автобиддера.
    """

    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(default=timezone.now)
    message = models.TextField()
    keyword = models.TextField(null=True, blank=True)  # Ключевая фраза мониторинга
    depth = models.IntegerField(blank=True, null=True, default=2)  # Глубина мониторинга
    destination = models.IntegerField(null=True, blank=True)  # Локация мониторинга
    product_id = models.IntegerField(null=True, blank=True)  # ID продукта
    position = models.IntegerField(null=True, blank=True)  # Позиция продукта
    clicks = models.IntegerField(null=True, blank=True)  # Количество кликов за сессию
    cards = models.IntegerField(null=True, blank=True)  # Количество корзин за сессию
    orders = models.IntegerField(null=True, blank=True)  # Количество заказов за сессию
    position_delta = models.IntegerField(null=True, blank=True)  # Изменение позиции продукта
    product_price = models.FloatField(null=True, blank=True)  # Текущая цена продукта
    average_cpm = models.FloatField(null=True, blank=True)  # Средний CPM на первой странице
    cpm = models.FloatField(null=True, blank=True)  # Текущий CPM для продукта
    before_average_cpm = models.FloatField(null=True, blank=True)  # Средний CPM у конкурентов
    min_cpm = models.FloatField(null=True, blank=True)  # Минимальный CPM на первой странице
    before_min_cpm = models.FloatField(null=True, blank=True)  # Минимальный CPM у конкурентов
    max_cpm = models.FloatField(null=True, blank=True)  # Максимальный CPM на первой странице
    before_max_cpm = models.FloatField(null=True, blank=True)  # Максимальный CPM у конкурентов
    average_advert_step_cost = models.FloatField(null=True, blank=True)  # Средняя стоимость за продвижение
    before_average_advert_step_cost = models.FloatField(null=True, blank=True)  # Средняя стоимость за продвижение у конкурентов
    advert_density = models.FloatField(null=True, blank=True)  # Коэффициент плотности рекламы
    advert_competitors_count = models.IntegerField(null=True, blank=True)  # Количество рекламных конкурентов
    advert_competitors_before = models.IntegerField(null=True, blank=True)  # Количество конкурентов перед продуктом
    advert_competitors_after = models.IntegerField(null=True, blank=True)  # Количество конкурентов после продукта
    advert_position = models.IntegerField(null=True, blank=True)  # Позиция продукта среди рекламы
    advert_count = models.IntegerField(null=True, blank=True)  # Количество рекламных карточек
    cpms = models.JSONField(verbose_name='cpms', default=list)  # Ставки CPM конкурентов
    advert_step_costs = models.JSONField(verbose_name='advert_step_costs', default=list)  # Стоимость за продвижение конкурентов
    advert_competitors = models.JSONField(verbose_name='advert_competitors', default=list)  # ID конкурентов
    bid = models.FloatField(null=True, blank=True)  # Текущая ставка автобиддера

    def current_user_has_access(self, request):
        """
        Проверяет, имеет ли текущий пользователь доступ к этому логу.

        Args:
            request (HttpRequest): Запрос от пользователя.

        Returns:
            bool: True, если пользователь имеет доступ, иначе False.
        """
        return self.campaign.store.user == request.user

    def __str__(self):
        """
        Возвращает строковое представление объекта.

        Returns:
            str: Строка, содержащая время записи и сообщение.
        """
        return f"{self.timestamp} - {self.message}"
