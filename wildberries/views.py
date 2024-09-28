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
    CreateAutoBidderSettingsForm, CreateMonitoringSettingsForm, AddKeywordsMonitoringForm
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

def monitoring_view(request, campaign_id):
    campaign = get_object_or_404(Campaign, pk=campaign_id)
    autobidder_settings, created = AutoBidderSettings.objects.get_or_create(campaign=campaign)

    if not autobidder_settings.current_user_has_access(request):
        return HttpResponseForbidden()

    if request.method == "POST":
        if 'create_settings' in request.POST:
            create_form = CreateMonitoringSettingsForm(request.POST, instance=autobidder_settings)
            if create_form.is_valid():
                create_form.save()

    create_form = CreateMonitoringSettingsForm(instance=autobidder_settings)

    context = {
        'campaign': campaign,
        'autobidder_settings': autobidder_settings,
        'create_form': create_form,
    }

    return render(request, 'wildberries/monitoring.html', context)


def monitoring_additional_words_view(request, campaign_id):
    campaign = get_object_or_404(Campaign, pk=campaign_id)

    autobidder_settings, created = AutoBidderSettings.objects.get_or_create(campaign=campaign)

    if not autobidder_settings.current_user_has_access(request):
        return HttpResponseForbidden()

    # Получаем или создаем объект KeywordData, связанный с кампанией
    keyword_data, created = KeywordData.objects.get_or_create(campaign=campaign)


    if request.method == "POST":
        if 'create_settings' in request.POST:
            create_form = AddKeywordsMonitoringForm(request.POST, instance=keyword_data)
            if create_form.is_valid():
                create_form.save()

    create_form = AddKeywordsMonitoringForm(instance=keyword_data)

    context = {
        'campaign': campaign,
        'autobidder_settings': autobidder_settings,
        'create_form': create_form,
    }

    return render(request, 'wildberries/monitoring_additional_words_view.html', context)



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
        task.watcher_data = data
        task.status = 'done'
        task.save()
        return JsonResponse({'message': 'Position recorded'})
    except PositionTrackingTask.DoesNotExist:
        return JsonResponse({'message': 'Task not found or not in progress'}, status=200)


@login_required()
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
        start_date = timezone.make_aware(
            datetime.strptime(date_range[0] + " 00:00:00", date_format),
            timezone.get_current_timezone()
        )
        end_date = timezone.make_aware(
            datetime.strptime(date_range[1] + " 23:59:59", date_format),
            timezone.get_current_timezone()
        )

        response_data = campaign.get_product_positions_for_chart(
            product_id=product_id,
            destination_id=destination,
            start_date=start_date,
            end_date=end_date,
            time_interval=time_interval
        )

        stat_data = campaign.get_stat_for_chart_by_product(
            product_id=product_id,
            start_date=start_date,
            end_date=end_date,
            time_interval=time_interval
        )

        combined_response_data = {
            'labels': response_data['labels'],
            'datasets': [
                response_data['datasets'][0],
                stat_data['datasets']
            ]
        }

        return JsonResponse(combined_response_data)
    return JsonResponse({}, status=400)


@login_required()
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

        data = campaign.get_stat_for_chart_by_product(
            product_id=product_id,
            start_date=start_date,
            end_date=end_date,
            time_interval=time_interval
        )

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
