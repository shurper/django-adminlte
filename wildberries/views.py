# wildberries/views.py
import json
from collections import defaultdict

from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.db import connection
from django.db.models.functions import Coalesce

from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Avg, Value, F, DecimalField, IntegerField
from django.db.models import Sum, FloatField, ExpressionWrapper, Case, When
from django.core.cache import cache

from wildberries.forms import SignUpForm, StoreForm, PositionRangeForm, IntraDayScheduleForm, WeeklyScheduleForm, \
    CreateAutoBidderSettingsForm
from wildberries.models import Store, Campaign, CampaignStatistic, PlatformStatistic, CampaignKeywordStatistic, \
    KeywordData, AutoCampaignKeywordStatistic, AutoBidderSettings, AutoBidderLog, PositionTrackingTask, PositionRange, \
    IntraDaySchedule, WeeklySchedule, ProductStatistic
from wildberries.utils import fetch_and_save_campaigns


@login_required
def index(request):
    return render(request, 'wildberries/index.html')


@login_required
def add_store(request):
    if request.method == 'POST':
        form = StoreForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            return redirect('stores')
    else:
        form = StoreForm(user=request.user)
    return render(request, 'wildberries/add_store.html', {'form': form})


@login_required
def edit_store(request, pk):
    store = get_object_or_404(Store, pk=pk)

    if not store.current_user_has_access(request):
        return HttpResponseForbidden()

    if request.method == 'POST':
        form = StoreForm(request.POST, instance=store)
        if form.is_valid():
            form.save()
            return redirect('stores')
        else:
            print(form.errors)  # Отладочный вывод ошибок формы
    else:
        form = StoreForm(instance=store)
    return render(request, 'wildberries/edit_store.html', {'form': form})


@login_required
def stores(request):
    stors = Store.objects.filter(user=request.user)
    return render(request, 'wildberries/store_list.html', {'stores': stors})


@login_required
def campaign_list(request, store_id):
    store = get_object_or_404(Store, id=store_id)

    if not store.current_user_has_access(request):
        return HttpResponseForbidden()

    campaigns = Campaign.objects.filter(store=store)
    return render(request, 'wildberries/campaign_list.html', {'store': store, 'campaigns': campaigns})


@login_required
def campaign_detail(request, campaign_id):
    campaign = get_object_or_404(Campaign, id=campaign_id)

    if not campaign.current_user_has_access(request):
        return HttpResponseForbidden()

    statistics = campaign.statistics.all().order_by('-date')
    return render(request, 'wildberries/campaign_detail.html', {'campaign': campaign, 'statistics': statistics})


@login_required
def update_campaigns(request, store_id):
    # TODO: check permissions
    fetch_and_save_campaigns(store_id)
    return redirect('store_campaigns', store_id=store_id)


@login_required
def store_campaigns(request, store_id):
    store = get_object_or_404(Store, pk=store_id)

    if not store.current_user_has_access(request):
        return HttpResponseForbidden()

    campaigns = Campaign.objects.filter(store=store)
    return render(request, 'wildberries/store_campaigns.html', {'store': store, 'campaigns': campaigns})


def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.refresh_from_db()  # Load the profile instance created by the signal
            user.email = form.cleaned_data.get('email')
            user.save()
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=user.username, password=raw_password)
            login(request, user)
            return redirect('index')  # Перенаправление на главную страницу после успешной регистрации
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})


@login_required
def platform_statistic_detail(request, campaign_statistic_id):
    campaign_statistic = get_object_or_404(CampaignStatistic, id=campaign_statistic_id)

    if not campaign_statistic.current_user_has_access(request):
        return HttpResponseForbidden()

    platforms = campaign_statistic.platforms.all()
    return render(request, 'wildberries/platform_statistic_detail.html',
                  {'campaign_statistic': campaign_statistic, 'platforms': platforms})


@login_required
def product_statistic_detail(request, platform_statistic_id):
    platform_statistic = get_object_or_404(PlatformStatistic, id=platform_statistic_id)

    if not platform_statistic.current_user_has_access(request):
        return HttpResponseForbidden()

    products = platform_statistic.products.all()
    return render(request, 'wildberries/product_statistic_detail.html',
                  {'platform_statistic': platform_statistic, 'products': products})


@login_required
def keyword_statistics(request, campaign_id):
    campaign = get_object_or_404(Campaign, id=campaign_id)
    keyword_statistics = CampaignKeywordStatistic.objects.filter(campaign=campaign).order_by('-date_received')

    if not keyword_statistics.current_user_has_access(request):
        return HttpResponseForbidden()

    keyword_data = KeywordData.objects.filter(campaign=campaign).first()
    return render(request, 'wildberries/keyword_statistics.html', {
        'campaign': campaign,
        'keyword_statistics': keyword_statistics,
        'keyword_data': keyword_data
    })


@login_required()
def auto_keyword_statistics(request, campaign_id):
    campaign = get_object_or_404(Campaign, id=campaign_id)
    keyword_statistics = AutoCampaignKeywordStatistic.objects.filter(campaign=campaign).order_by('-date_recorded')

    if not keyword_statistics.current_user_has_access(request):
        return HttpResponseForbidden()

    return render(request, 'wildberries/auto_keyword_statistics.html', {
        'campaign': campaign,
        'keyword_statistics': keyword_statistics,
    })


@login_required()
def autobidder_view(request, campaign_id):
    campaign = get_object_or_404(Campaign, pk=campaign_id)
    autobidder_settings, created = AutoBidderSettings.objects.get_or_create(campaign=campaign)

    if not autobidder_settings.current_user_has_access(request):
        return HttpResponseForbidden()

    if request.method == "POST":
        if 'create_settings' in request.POST:
            create_form = CreateAutoBidderSettingsForm(request.POST, instance=autobidder_settings)
            if create_form.is_valid():
                create_form.save()
        elif 'position_ranges' in request.POST:
            position_form = PositionRangeForm(request.POST)
            if position_form.is_valid():
                PositionRange.objects.create(
                    autobidder_settings=autobidder_settings,
                    start_position=position_form.cleaned_data['start_position'],
                    end_position=position_form.cleaned_data['end_position'],
                    bid=position_form.cleaned_data['bid']
                )
            if 'delete_range' in request.POST:
                range_id = request.POST.get('delete_range')
                PositionRange.objects.filter(id=range_id, autobidder_settings=autobidder_settings).delete()

        elif 'edit_range' in request.POST:
            range_id = request.POST.get('edit_range')
            range_instance = get_object_or_404(PositionRange, id=range_id, autobidder_settings=autobidder_settings)
            position_form = PositionRangeForm(request.POST, instance=range_instance)
            if position_form.is_valid():
                position_form.save()
        elif 'intra_day_schedule' in request.POST:
            intra_day_form = IntraDayScheduleForm(request.POST)
            if intra_day_form.is_valid():
                IntraDaySchedule.objects.create(
                    autobidder_settings=autobidder_settings,
                    start_time=intra_day_form.cleaned_data['start_time'],
                    end_time=intra_day_form.cleaned_data['end_time']
                )
            if 'delete_intra_day_schedule' in request.POST:
                intra_day_schedule_id = request.POST.get('delete_intra_day_schedule')
                IntraDaySchedule.objects.filter(id=intra_day_schedule_id,
                                                autobidder_settings=autobidder_settings).delete()
        elif 'edit_intra_day_schedule' in request.POST:
            intra_day_schedule_id = request.POST.get('edit_intra_day_schedule')
            intra_day_schedule_instance = get_object_or_404(IntraDaySchedule, id=intra_day_schedule_id,
                                                            autobidder_settings=autobidder_settings)
            IntraDaySchedule_form = IntraDayScheduleForm(request.POST, instance=intra_day_schedule_instance)
            if IntraDaySchedule_form.is_valid():
                IntraDaySchedule_form.save()
        elif 'weekly_schedule' in request.POST:
            weekly_form = WeeklyScheduleForm(request.POST)
            if weekly_form.is_valid():
                WeeklySchedule.objects.create(
                    autobidder_settings=autobidder_settings,
                    day_of_week=weekly_form.cleaned_data['day_of_week']
                )
            if 'delete_weekly_schedule' in request.POST:
                weekly_schedule_id = request.POST.get('delete_weekly_schedule')
                WeeklySchedule.objects.filter(id=weekly_schedule_id, autobidder_settings=autobidder_settings).delete()
        elif 'edit_weekly_schedule' in request.POST:
            weekly_schedule_id = request.POST.get('edit_weekly_schedule')
            weekly_schedule_instance = get_object_or_404(WeeklySchedule, id=weekly_schedule_id,
                                                         autobidder_settings=autobidder_settings)
            weekly_schedule_form = WeeklyScheduleForm(request.POST, instance=weekly_schedule_instance)
            if weekly_schedule_form.is_valid():
                weekly_schedule_form.save()

    create_form = CreateAutoBidderSettingsForm(instance=autobidder_settings)
    position_form = PositionRangeForm()
    intra_day_form = IntraDayScheduleForm()
    weekly_form = WeeklyScheduleForm()
    logs = AutoBidderLog.objects.filter(campaign=campaign).order_by('-timestamp')

    current_position_ranges = PositionRange.objects.filter(autobidder_settings=autobidder_settings)
    current_intra_day_schedule = IntraDaySchedule.objects.filter(autobidder_settings=autobidder_settings)
    current_weekly_schedule = WeeklySchedule.objects.filter(autobidder_settings=autobidder_settings)

    context = {
        'campaign': campaign,
        'autobidder_settings': autobidder_settings,
        'create_form': create_form,
        'position_form': position_form,
        'intra_day_form': intra_day_form,
        'weekly_form': weekly_form,
        'logs': logs,
        'current_position_ranges': current_position_ranges,
        'current_intra_day_schedule': current_intra_day_schedule,
        'current_weekly_schedule': current_weekly_schedule
    }

    return render(request, 'wildberries/autobidder.html', context)


@csrf_exempt
def observer_get_task(request):
    # TODO: check permissions
    tasks = PositionTrackingTask.objects.filter(status='request').order_by('created_at')

    if tasks.exists():
        response_data = {}

        for task in tasks:
            destination = task.destination
            keyword = task.keyword
            product_id = task.product_id
            depth = task.depth

            if destination not in response_data:
                response_data[destination] = {}

            if keyword not in response_data[destination]:
                response_data[destination][keyword] = {
                    "items": [],
                    "max_page": depth
                }

            response_data[destination][keyword]["items"].append(product_id)

        # Обновляем статус всех задач
        tasks.update(status='in_progress')
        print(response_data)
        return JsonResponse(response_data)

    return JsonResponse({}, status=404)


@csrf_exempt
def observer_report_position(request):
    # TODO: check permissions
    data = json.loads(request.body)
    print(f"Report received {data}")
    try:
        page = data['page']
        items_per_page = 100

        task = PositionTrackingTask.objects.filter(
            keyword=data['query'],
            product_id=data['article'],
            status='in_progress',
            destination=data['dest']
        ).latest('created_at')
        task.actual_position = items_per_page * (page - 1) + data['position']
        task.status = 'done'
        task.save()
        return JsonResponse({'message': 'Position recorded'})
    except PositionTrackingTask.DoesNotExist:
        return JsonResponse({'message': 'Task not found or not in progress'}, status=200)


def api_get_chart_data(request):
    if request.method == 'POST':
        time_interval = request.POST.get('time_interval')
        date_range = request.POST.get('date_range').split(' - ')
        destination = request.POST.get('destination')
        product_id = request.POST.get('product_id')
        campaign_id = request.POST.get('campaign_id')

        campaign = get_object_or_404(Campaign, pk=campaign_id)

        if not campaign.current_user_has_access(request):
            return HttpResponseForbidden()

        date_format = '%d-%m-%Y %H:%M:%S'
        start_date = timezone.make_aware(datetime.strptime(date_range[0] + " 00:00:00", date_format),
                                         timezone.get_current_timezone())
        end_date = timezone.make_aware(datetime.strptime(date_range[1] + " 23:59:59", date_format),
                                       timezone.get_current_timezone())
        now = timezone.now()

        # Group logs by the chosen time interval and calculate average position
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

        # Extract all logs at once and process in memory
        logs = AutoBidderLog.objects.filter(
            timestamp__range=(start_date, end_date),
            destination=destination,
            product_id=product_id,
            campaign_id=campaign_id
        ).values('timestamp', 'keyword', 'position')

        # Prepare a dict to store logs by intervals
        interval_logs = defaultdict(list)

        for log in logs:
            interval_start = (log['timestamp'] - start_date) // time_delta * time_delta + start_date
            interval_logs[interval_start].append(log)

        keywords = set(log['keyword'] for log in logs)
        current_time = start_date

        while current_time <= end_date:
            next_time = current_time + time_delta
            labels.append(current_time.strftime('%d-%m-%Y %H:%M:%S'))

            if current_time <= now:
                cache_key = f'{campaign_id}_{destination}_{product_id}_{current_time}_{next_time}'
                if current_time != now:
                    interval_data = cache.get(cache_key)
                else:
                    interval_data = None

                if interval_data is None:
                    interval_data = defaultdict(list)

                    for log in interval_logs[current_time]:
                        if log['position'] <= 200:
                            interval_data[log['keyword']].append(log['position'])

                    for keyword, positions in interval_data.items():
                        avg_position = sum(positions) / len(positions) if positions else None
                        interval_data[keyword] = avg_position

                    cache.set(cache_key, interval_data, timeout=360000)  # Cache for 1 hour

                for keyword in keywords:
                    avg_position = interval_data.get(keyword, None)
                    datasets[keyword]['label'] = keyword
                    datasets[keyword]['data'].append(avg_position)
            else:
                for keyword in keywords:
                    datasets[keyword]['data'].append(None)

            current_time = next_time

        response_data = {
            'labels': labels,
            'datasets': list(datasets.values())
        }

        return JsonResponse(response_data)
    return JsonResponse({}, status=400)


def api_get_stat_chart_data(request):
    if request.method == 'POST':
        time_interval = request.POST.get('time_interval')
        date_range = request.POST.get('date_range').split(' - ')
        product_id = request.POST.get('product_id')
        campaign_id = request.POST.get('campaign_id')

        campaign = get_object_or_404(Campaign, pk=campaign_id)

        if not campaign.current_user_has_access(request):
            return HttpResponseForbidden()

        date_format = '%d-%m-%Y %H:%M:%S'
        date_range[0] = date_range[0] + " 00:00:00"
        date_range[1] = date_range[1] + " 23:59:59"
        start_date = datetime.strptime(date_range[0], date_format)
        end_date = datetime.strptime(date_range[1], date_format)

        start_date = timezone.make_aware(start_date, timezone.get_current_timezone())
        end_date = timezone.make_aware(end_date, timezone.get_current_timezone())

        base_stats = (
            ProductStatistic.objects
            .filter(
                nm_id=product_id,
                platform_statistic__campaign_statistic__campaign=campaign,
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
                {'label': 'Просмотры', 'data': [], 'borderColor': 'rgba(75, 192, 192, 1)', 'fill': False, 'hidden': True},
                {'label': 'Клики', 'data': [], 'borderColor': 'rgba(54, 162, 235, 1)', 'fill': False},
                {'label': 'CTR (кликабельность)', 'data': [], 'borderColor': 'rgba(255, 206, 86, 1)', 'fill': False},
                {'label': 'CPC (цена клика)', 'data': [], 'borderColor': 'rgba(75, 192, 192, 1)', 'fill': False},
                {'label': 'Затраты', 'data': [], 'borderColor': 'rgba(153, 102, 255, 1)', 'fill': False,  'hidden': True},
                {'label': 'Корзины', 'data': [], 'borderColor': 'rgba(255, 159, 64, 1)', 'fill': False},
                {'label': 'Заказы', 'data': [], 'borderColor': 'rgba(199, 199, 199, 1)', 'fill': False},
                {'label': 'Корзины из аналитики', 'data': [], 'borderColor': 'rgba(255, 99, 132, 1)', 'fill': False},
                {'label': 'Заказы из аналитики', 'data': [], 'borderColor': 'rgba(54, 162, 235, 1)', 'fill': False},
                {'label': 'CR (уровень конверсии - "заказы/клики")', 'data': [], 'borderColor': 'rgba(75, 192, 192, 1)', 'fill': False},
                {'label': 'Заказано товаров', 'data': [], 'borderColor': 'rgba(255, 206, 86, 1)', 'fill': False},
                {'label': 'Сумма заказов', 'data': [], 'borderColor': 'rgba(153, 102, 255, 1)', 'fill': False,  'hidden': True},
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

            data['labels'].append(current_time.strftime('%d-%m-%Y %H:%M:%S'))
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

        return JsonResponse(data)


@login_required()
def api_get_destinations(request):
    destinations = AutoBidderLog.objects.values_list('destination', flat=True).distinct()
    data = [{'id': dest, 'name': f'Destination {dest}'} for dest in destinations]
    return JsonResponse(data, safe=False)


@login_required()
def api_get_products(request):
    campaign_id = request.GET.get('campaign_id')
    if not campaign_id:
        return JsonResponse({'error': 'Campaign ID is required'}, status=400)

    try:
        campaign = Campaign.objects.get(id=campaign_id)

        if not campaign.current_user_has_access(request):
            return HttpResponseForbidden()

    except Campaign.DoesNotExist:
        return JsonResponse({'error': 'Campaign not found or access denied'}, status=404)

    products = AutoBidderLog.objects.filter(campaign=campaign).values_list('product_id', flat=True).distinct()
    data = [{'id': prod, 'name': f'Product {prod}'} for prod in products]
    return JsonResponse(data, safe=False)
