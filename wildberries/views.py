# wildberries/views.py
import json

from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required

from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Avg
from django.core.cache import cache

from wildberries.forms import SignUpForm, StoreForm, PositionRangeForm, IntraDayScheduleForm, WeeklyScheduleForm, \
    CreateAutoBidderSettingsForm
from wildberries.models import Store, Campaign, CampaignStatistic, PlatformStatistic, CampaignKeywordStatistic, \
    KeywordData, AutoCampaignKeywordStatistic, AutoBidderSettings, AutoBidderLog, PositionTrackingTask, PositionRange, \
    IntraDaySchedule, WeeklySchedule
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
    campaigns = Campaign.objects.filter(store=store)
    return render(request, 'wildberries/campaign_list.html', {'store': store, 'campaigns': campaigns})


@login_required
def campaign_detail(request, campaign_id):
    campaign = get_object_or_404(Campaign, id=campaign_id)
    statistics = campaign.statistics.all().order_by('-date')
    return render(request, 'wildberries/campaign_detail.html', {'campaign': campaign, 'statistics': statistics})


@login_required
def update_campaigns(request, store_id):
    fetch_and_save_campaigns(store_id)
    return redirect('store_campaigns', store_id=store_id)


# def store_campaigns(request, store_id):
#     store = Store.objects.get(id=store_id)
#     campaigns = Campaign.objects.filter(store=store)
#     return render(request, 'wildberries/campaign_list.html', {'store': store, 'campaigns': campaigns})
@login_required
def store_campaigns(request, store_id):
    store = get_object_or_404(Store, pk=store_id)
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
    platforms = campaign_statistic.platforms.all()
    return render(request, 'wildberries/platform_statistic_detail.html',
                  {'campaign_statistic': campaign_statistic, 'platforms': platforms})


@login_required
def product_statistic_detail(request, platform_statistic_id):
    platform_statistic = get_object_or_404(PlatformStatistic, id=platform_statistic_id)
    products = platform_statistic.products.all()
    return render(request, 'wildberries/product_statistic_detail.html',
                  {'platform_statistic': platform_statistic, 'products': products})


@login_required
def keyword_statistics(request, campaign_id):
    campaign = get_object_or_404(Campaign, id=campaign_id)
    keyword_statistics = CampaignKeywordStatistic.objects.filter(campaign=campaign).order_by('-date_received')
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
    return render(request, 'wildberries/auto_keyword_statistics.html', {
        'campaign': campaign,
        'keyword_statistics': keyword_statistics,
    })

@login_required()
def autobidder_view(request, campaign_id):
    campaign = get_object_or_404(Campaign, pk=campaign_id)
    autobidder_settings, created = AutoBidderSettings.objects.get_or_create(campaign=campaign)

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
                IntraDaySchedule.objects.filter(id=intra_day_schedule_id, autobidder_settings=autobidder_settings).delete()
        elif 'edit_intra_day_schedule' in request.POST:
            intra_day_schedule_id = request.POST.get('edit_intra_day_schedule')
            intra_day_schedule_instance = get_object_or_404(IntraDaySchedule, id=intra_day_schedule_id, autobidder_settings=autobidder_settings)
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



# @csrf_exempt
# def observer_get_task(request):
#     task = PositionTrackingTask.objects.filter(status='request').order_by('created_at').first()
#     if task:
#         task.status = 'in_progress'
#         task.save()
#         destination = task.destination
#         return JsonResponse({
#             destination: {
#                 task.keyword: {
#                     "items": [task.product_id],
#                     "max_page": task.depth
#                 }
#             }
#         })
#     return JsonResponse({}, status=404)


@csrf_exempt
def observer_get_task(request):
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
        task.actual_position = items_per_page * (page -1) + data['position']
        task.status = 'done'
        task.save()
        return JsonResponse({'message': 'Position recorded'})
    except PositionTrackingTask.DoesNotExist:
        return JsonResponse({'message': 'Task not found or not in progress'}, status=200)

# @login_required()
# def api_get_chart_data(request):
#     if request.method == 'POST':
#         time_interval = request.POST.get('time_interval')
#         date_range = request.POST.get('date_range').split(' - ')
#         destination = request.POST.get('destination')
#         product_id = request.POST.get('product_id')
#
#         date_format = '%d-%m-%Y %H:%M:%S'
#         date_range[0] = date_range[0] + " 00:00:00"
#         date_range[1] = date_range[1] + " 23:59:59"
#         start_date = datetime.strptime(date_range[0], date_format)
#         end_date = datetime.strptime(date_range[1], date_format)
#
#         # Make the datetime objects timezone-aware
#         start_date = timezone.make_aware(start_date, timezone.get_current_timezone())
#         end_date = timezone.make_aware(end_date, timezone.get_current_timezone())
#
#         # Filter logs based on user selection
#         logs = AutoBidderLog.objects.filter(
#             timestamp__range=(start_date, end_date),
#             destination=destination,
#             product_id=product_id
#         )
#
#
#
#         # Group logs by the chosen time interval and calculate average position
#         time_delta = timedelta(hours=1)
#         if time_interval == '5m':
#             time_delta = timedelta(minutes=5)
#         elif time_interval == '15m':
#             time_delta = timedelta(minutes=15)
#         elif time_interval == '1h':
#             time_delta = timedelta(hours=1)
#         elif time_interval == '4h':
#             time_delta = timedelta(hours=4)
#         elif time_interval == '1d':
#             time_delta = timedelta(days=1)
#         elif time_interval == '1w':
#             time_delta = timedelta(weeks=1)
#         elif time_interval == '1M':
#             time_delta = timedelta(days=30)
#
#         labels = []
#         datasets = {}
#
#         current_time = start_date
#         while current_time <= end_date:
#             next_time = current_time + time_delta
#             labels.append(current_time.strftime('%d-%m-%Y %H:%M:%S'))
#
#             interval_logs = logs.filter(timestamp__range=(current_time, next_time))
#             keywords = interval_logs.values('keyword').distinct()
#
#             for keyword in keywords:
#                 keyword_logs = interval_logs.filter(keyword=keyword['keyword'], position__lte=200)
#                 avg_position = keyword_logs.aggregate(Avg('position'))['position__avg']
#
#                 if keyword['keyword'] not in datasets:
#                     datasets[keyword['keyword']] = {
#                         'label': keyword['keyword'],
#                         'data': []
#                     }
#
#                 datasets[keyword['keyword']]['data'].append(avg_position)
#
#             current_time = next_time
#
#         # Format data for Chart.js
#         response_data = {
#             'labels': labels,
#             'datasets': list(datasets.values())
#         }
#
#         return JsonResponse(response_data)
#     return JsonResponse({}, status=400)


# @login_required()
# def api_get_chart_data(request):
#     if request.method == 'POST':
#         time_interval = request.POST.get('time_interval')
#         date_range = request.POST.get('date_range').split(' - ')
#         destination = request.POST.get('destination')
#         product_id = request.POST.get('product_id')
#
#         date_format = '%d-%m-%Y %H:%M:%S'
#         date_range[0] = date_range[0] + " 00:00:00"
#         date_range[1] = date_range[1] + " 23:59:59"
#         start_date = datetime.strptime(date_range[0], date_format)
#         end_date = datetime.strptime(date_range[1], date_format)
#
#         # Make the datetime objects timezone-aware
#         start_date = timezone.make_aware(start_date, timezone.get_current_timezone())
#         end_date = timezone.make_aware(end_date, timezone.get_current_timezone())
#         now = timezone.now()
#
#         # Filter logs based on user selection
#         logs = AutoBidderLog.objects.filter(
#             timestamp__range=(start_date, end_date),
#             destination=destination,
#             product_id=product_id
#         )
#
#         # Group logs by the chosen time interval and calculate average position
#         time_deltas = {
#             '5m': timedelta(minutes=5),
#             '15m': timedelta(minutes=15),
#             '1h': timedelta(hours=1),
#             '4h': timedelta(hours=4),
#             '1d': timedelta(days=1),
#             '1w': timedelta(weeks=1),
#             '1M': timedelta(days=30),
#         }
#         time_delta = time_deltas.get(time_interval, timedelta(hours=1))
#
#         labels = []
#         datasets = {}
#
#         keywords = logs.values('keyword').distinct()
#         current_time = start_date
#         while current_time <= end_date:
#             next_time = current_time + time_delta
#             labels.append(current_time.strftime('%d-%m-%Y %H:%M:%S'))
#
#             if current_time <= now:
#                 interval_logs = logs.filter(timestamp__gte=current_time, timestamp__lt=next_time)
#
#                 for keyword in keywords:
#                     keyword_logs = interval_logs.filter(keyword=keyword['keyword'], position__lte=200)
#                     avg_position = keyword_logs.aggregate(Avg('position'))['position__avg']
#
#                     if keyword['keyword'] not in datasets:
#                         datasets[keyword['keyword']] = {
#                             'label': keyword['keyword'],
#                             'data': []
#                         }
#
#                     datasets[keyword['keyword']]['data'].append(avg_position if avg_position is not None else None)
#             else:
#                 for keyword in keywords:
#                     if keyword['keyword'] not in datasets:
#                         datasets[keyword['keyword']] = {
#                             'label': keyword['keyword'],
#                             'data': []
#                         }
#                     datasets[keyword['keyword']]['data'].append(None)
#
#             current_time = next_time
#
#         # Format data for Chart.js
#         response_data = {
#             'labels': labels,
#             'datasets': list(datasets.values())
#         }
#
#         return JsonResponse(response_data)
#     return JsonResponse({}, status=400)

@login_required()
# def api_get_chart_data(request):
#     if request.method == 'POST':
#         time_interval = request.POST.get('time_interval')
#         date_range = request.POST.get('date_range').split(' - ')
#         destination = request.POST.get('destination')
#         product_id = request.POST.get('product_id')
#
#         date_format = '%d-%m-%Y %H:%M:%S'
#         date_range[0] = date_range[0] + " 00:00:00"
#         date_range[1] = date_range[1] + " 23:59:59"
#         start_date = datetime.strptime(date_range[0], date_format)
#         end_date = datetime.strptime(date_range[1], date_format)
#
#         # Make the datetime objects timezone-aware
#         start_date = timezone.make_aware(start_date, timezone.get_current_timezone())
#         end_date = timezone.make_aware(end_date, timezone.get_current_timezone())
#         now = timezone.now()
#
#         # Determine the truncation function based on the time interval
#         trunc_map = {
#             '5m': TruncMinute,
#             '15m': TruncMinute,
#             '1h': TruncHour,
#             '4h': TruncHour,
#             '1d': TruncDay,
#             '1w': TruncWeek,
#             '1M': TruncMonth,
#         }
#         trunc_func = trunc_map.get(time_interval, TruncHour)
#
#         # Filter logs based on user selection and aggregate data
#         logs = (
#             AutoBidderLog.objects.filter(
#                 timestamp__range=(start_date, end_date),
#                 destination=destination,
#                 product_id=product_id,
#                 position__lte=200
#             )
#             .annotate(interval_start=trunc_func('timestamp'))
#             .values('interval_start', 'keyword')
#             .annotate(avg_position=Avg('position'))
#             .order_by('interval_start')
#         )
#
#         # Prepare labels and datasets
#         labels = []
#         datasets = {}
#
#         # Create a dictionary to hold the aggregated data
#         data = {}
#         for log in logs:
#             interval_start = log['interval_start']
#             keyword = log['keyword']
#             avg_position = log['avg_position']
#
#             if interval_start not in data:
#                 data[interval_start] = {}
#             data[interval_start][keyword] = avg_position
#
#         # Generate the time intervals and fill the datasets
#         current_time = start_date
#         time_delta = timedelta(minutes=5 if time_interval == '5m' else (
#             15 if time_interval == '15m' else (
#                 60 if time_interval == '1h' else (
#                     240 if time_interval == '4h' else (
#                         1440 if time_interval == '1d' else (
#                             10080 if time_interval == '1w' else 43200
#                         )
#                     )
#                 )
#             )
#         ))
#
#         while current_time <= end_date:
#             labels.append(current_time.strftime('%d-%m-%Y %H:%M:%S'))
#             for keyword in data.get(current_time, {}):
#                 if keyword not in datasets:
#                     datasets[keyword] = {
#                         'label': keyword,
#                         'data': []
#                     }
#                 datasets[keyword]['data'].append(data[current_time].get(keyword, None))
#
#             # Fill missing data with None
#             for keyword in datasets:
#                 if current_time not in data or keyword not in data[current_time]:
#                     datasets[keyword]['data'].append(None)
#
#             current_time += time_delta
#
#         # Format data for Chart.js
#         response_data = {
#             'labels': labels,
#             'datasets': list(datasets.values())
#         }
#
#         return JsonResponse(response_data)
#     return JsonResponse({}, status=400)

@login_required()
def api_get_chart_data(request):
    if request.method == 'POST':
        time_interval = request.POST.get('time_interval')
        date_range = request.POST.get('date_range').split(' - ')
        destination = request.POST.get('destination')
        product_id = request.POST.get('product_id')

        date_format = '%d-%m-%Y %H:%M:%S'
        date_range[0] = date_range[0] + " 00:00:00"
        date_range[1] = date_range[1] + " 23:59:59"
        start_date = datetime.strptime(date_range[0], date_format)
        end_date = datetime.strptime(date_range[1], date_format)

        # Make the datetime objects timezone-aware
        start_date = timezone.make_aware(start_date, timezone.get_current_timezone())
        end_date = timezone.make_aware(end_date, timezone.get_current_timezone())
        now = timezone.now()

        # Filter logs based on user selection
        logs = AutoBidderLog.objects.filter(
            timestamp__range=(start_date, end_date),
            destination=destination,
            product_id=product_id
        )

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
        datasets = {}

        keywords = logs.values('keyword').distinct()
        current_time = start_date

        while current_time <= end_date:
            next_time = current_time + time_delta
            labels.append(current_time.strftime('%d-%m-%Y %H:%M:%S'))

            if current_time <= now:
                cache_key = f'{destination}_{product_id}_{current_time}_{next_time}'
                interval_data = cache.get(cache_key)

                if interval_data is None:
                    interval_logs = logs.filter(timestamp__gte=current_time, timestamp__lt=next_time)
                    interval_data = {}

                    for keyword in keywords:
                        keyword_logs = interval_logs.filter(keyword=keyword['keyword'], position__lte=200)
                        avg_position = keyword_logs.aggregate(Avg('position'))['position__avg']
                        interval_data[keyword['keyword']] = avg_position if avg_position is not None else None

                    cache.set(cache_key, interval_data, timeout=360000)  # Cache for 1 hour

                for keyword, avg_position in interval_data.items():
                    if keyword not in datasets:
                        datasets[keyword] = {
                            'label': keyword,
                            'data': []
                        }
                    datasets[keyword]['data'].append(avg_position)
            else:
                for keyword in keywords:
                    if keyword['keyword'] not in datasets:
                        datasets[keyword['keyword']] = {
                            'label': keyword['keyword'],
                            'data': []
                        }
                    datasets[keyword['keyword']]['data'].append(None)

            current_time = next_time

        # Format data for Chart.js
        response_data = {
            'labels': labels,
            'datasets': list(datasets.values())
        }

        return JsonResponse(response_data)
    return JsonResponse({}, status=400)


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
    except Campaign.DoesNotExist:
        return JsonResponse({'error': 'Campaign not found or access denied'}, status=404)

    products = AutoBidderLog.objects.filter(campaign=campaign).values_list('product_id', flat=True).distinct()
    data = [{'id': prod, 'name': f'Product {prod}'} for prod in products]
    return JsonResponse(data, safe=False)