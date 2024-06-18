# wildberries/views.py
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404

from wildberries.forms import SignUpForm, StoreForm
from wildberries.models import Store, Campaign, CampaignStatistic, PlatformStatistic
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
    return render(request, 'wildberries/platform_statistic_detail.html', {'campaign_statistic': campaign_statistic, 'platforms': platforms})

@login_required
def product_statistic_detail(request, platform_statistic_id):
    platform_statistic = get_object_or_404(PlatformStatistic, id=platform_statistic_id)
    products = platform_statistic.products.all()
    return render(request, 'wildberries/product_statistic_detail.html', {'platform_statistic': platform_statistic, 'products': products})