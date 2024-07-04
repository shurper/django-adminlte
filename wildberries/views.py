# wildberries/views.py
import json

from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods


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
        form = StoreForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('stores')
    else:
        form = StoreForm()
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
        return JsonResponse({'message': 'Task not found or not in progress'}, status=404)