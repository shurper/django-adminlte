# wildberries/utils.py
from datetime import date, datetime, timedelta

import requests
from django.utils import timezone
from notifications.signals import notify

from .models import Store, Campaign, Subject, Menu, UnitedParam, CampaignStatistic, PlatformStatistic, ProductStatistic, \
    Set, KeywordData, CampaignKeywordStatistic, AutoCampaignKeywordStatistic
from .notifications import notify_wb


def get_campaign_list(store):
    url = 'https://advert-api.wildberries.ru/adv/v1/promotion/count'
    headers = {
        'accept': 'application/json',
        'Authorization': store.wildberries_api_key
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f'Token: {store.wildberries_api_key}')
        print(f'Error fetching campaign list: {response.json()}')
        if response.status_code == 401:
            notify_wb(
                store.user,
                store.user,
                'Обновите API-ключ',
                'Мы не можем получить данные вашего магазина, потому что API-ключ Wildberries не принимается. Пожалуйста, обновите ключ в настройках магазина.',
                {'store_id': store.id}
            )
        return None


def get_campaign_details(store, advert_ids):
    url = 'https://advert-api.wildberries.ru/adv/v1/promotion/adverts?order=create&direction=asc'
    headers = {
        'accept': 'application/json',
        'Authorization': store.wildberries_api_key,
        'Content-Type': 'application/json'
    }
    response = requests.post(url, headers=headers, json=advert_ids)
    if response.status_code == 200:
        return response.json()
    else:
        print(f'Error fetching campaign details: {response.json()}')
        if response.status_code == 401:
            notify_wb(
                store.user,
                store.user,
                'Обновите API-ключ',
                'Мы не можем получить данные вашего магазина, потому что API-ключ Wildberries не принимается. Пожалуйста, обновите ключ в настройках магазина.',
                {'store_id': store.id}
            )
        return None


def save_campaign_details(store, campaign_data):
    for campaign in campaign_data:
        advert_id = campaign['advertId']
        name = campaign['name']
        start_time = campaign['startTime']
        end_time = campaign['endTime']
        create_time = campaign['createTime']
        change_time = campaign['changeTime']
        daily_budget = campaign['dailyBudget']
        status = campaign['status']
        type = campaign['type']
        payment_type = campaign['paymentType']

        # Обработка "поиск + каталог" кампании
        if type == 9:
            search_pluse_state = campaign.get('searchPluseState', False)
            united_params = campaign.get('unitedParams', [])
            campaign_obj, created = Campaign.objects.update_or_create(
                advert_id=advert_id,
                defaults={
                    'store': store,
                    'name': name,
                    'start_time': start_time,
                    'end_time': end_time,
                    'create_time': create_time,
                    'change_time': change_time,
                    'search_pluse_state': search_pluse_state,
                    'daily_budget': daily_budget,
                    'status': status,
                    'type': type,
                    'payment_type': payment_type
                }
            )

            for param in united_params:
                catalog_cpm = param['catalogCPM']
                search_cpm = param['searchCPM']
                subject_data = param.get('subject', {})
                if subject_data.get('name', '') == '':
                    continue
                menus_data = param.get('menus', [])
                nms = param.get('nms', [])

                subject_obj, _ = Subject.objects.get_or_create(
                    id=subject_data['id'],
                    defaults={'name': subject_data['name']}
                )

                united_param_obj, created = UnitedParam.objects.update_or_create(
                    campaign=campaign_obj,
                    subject=subject_obj,
                    defaults={
                        'catalog_cpm': catalog_cpm,
                        'search_cpm': search_cpm,
                        'nms': nms
                    }
                )

                # Используйте set() для установки значений ManyToMany поля
                menu_objs = []
                for menu_data in menus_data:
                    menu_obj, _ = Menu.objects.get_or_create(
                        id=menu_data['id'],
                        defaults={'name': menu_data['name']}
                    )
                    menu_objs.append(menu_obj)
                united_param_obj.menus.set(menu_objs)

        # Обработка "автоматическая кампания"
        elif type == 8:
            auto_params = campaign.get('autoParams', {})
            subject_data = auto_params.get('subject', {})
            if subject_data.get('name', '') == '':
                continue
            sets_data = auto_params.get('sets', [])
            active = auto_params.get('active', {})
            nms = auto_params.get('nms', [])
            nmCPM = auto_params.get('nmCPM', [])

            campaign_obj, created = Campaign.objects.update_or_create(
                advert_id=advert_id,
                defaults={
                    'store': store,
                    'name': name,
                    'start_time': start_time,
                    'end_time': end_time,
                    'create_time': create_time,
                    'change_time': change_time,
                    'daily_budget': daily_budget,
                    'status': status,
                    'type': type,
                    'payment_type': payment_type
                }
            )

            subject_obj, _ = Subject.objects.get_or_create(
                id=subject_data['id'],
                defaults={'name': subject_data.get('name', 'Скоро появится')}
            )

            united_param_obj, created = UnitedParam.objects.update_or_create(
                campaign=campaign_obj,
                subject=subject_obj,
                defaults={
                    'catalog_cpm': 0,
                    'search_cpm': 0,
                    'nms': nms,
                    'nmCPMs': nmCPM,  # Добавлено для полноты
                }
            )

            set_objs = []
            for set_data in sets_data:
                set_obj, _ = Set.objects.get_or_create(
                    id=set_data['id'],
                    defaults={'name': set_data['name']}
                )
                set_objs.append(set_obj)
            united_param_obj.sets.set(set_objs)

            # Обновление активного состояния кампании
            united_param_obj.active_carousel = active.get('carousel', False)
            united_param_obj.active_recom = active.get('recom', False)
            united_param_obj.active_booster = active.get('booster', False)
            united_param_obj.save()

        else:
            print(f'Unsupported campaign type {type}')


def fetch_and_save_campaigns(store_id):
    try:
        print(f'Store with id {store_id} prepared to update')
        store = Store.objects.get(id=store_id)

        campaign_list_data = get_campaign_list(store)
        # print(campaign_list_data)
        if campaign_list_data:
            advert_ids = []
            for advert in campaign_list_data['adverts']:
                advert_ids.extend([item['advertId'] for item in advert['advert_list']])
            campaign_details_data = get_campaign_details(store, advert_ids)
            if campaign_details_data:
                save_campaign_details(store, campaign_details_data)
    except Store.DoesNotExist:
        print(f'Store with id {store_id} does not exist')


def get_campaign_statistics(store, advert_ids):
    url = 'https://advert-api.wildberries.ru/adv/v2/fullstats'
    headers = {
        'accept': 'application/json',
        'Authorization': store.wildberries_api_key,
        'Content-Type': 'application/json'
    }
    # Get today's date in the format Year-Month-Day
    today_date = datetime.now().strftime('%Y-%m-%d')

    # Create the JSON payload with the updated format
    payload = [{"id": advert_id, "dates": [today_date, today_date]} for advert_id in advert_ids]

    response = requests.post(url, headers=headers, json=payload)

    print(response.json())
    if response.status_code == 200:
        return response.json()
    else:
        print(f'Error fetching campaign statistics: {response.json()}')
        if response.status_code == 401:
            notify_wb(
                store.user,
                store.user,
                'Обновите API-ключ',
                'Мы не можем получить данные вашего магазина, потому что API-ключ Wildberries не принимается. Пожалуйста, обновите ключ в настройках магазина.',
                {'store_id': store.id}
            )
        return None


def save_campaign_statistics(store):
    campaigns = Campaign.objects.filter(store=store)
    advert_ids = [campaign.advert_id for campaign in campaigns]
    statistics = get_campaign_statistics(store, advert_ids)

    if statistics:
        for stat in statistics:
            campaign = Campaign.objects.get(advert_id=stat['advertId'])

            previous_stat = CampaignStatistic.objects.filter(campaign=campaign).order_by('-date').first()

            campaign_stat = CampaignStatistic(
                campaign=campaign,
                date=timezone.now(),
                views=stat['views'],
                clicks=stat['clicks'],
                ctr=stat['ctr'],
                cpc=stat['cpc'],
                sum=stat['sum'],
                atbs=stat['atbs'],
                orders=stat['orders'],
                cr=stat['cr'],
                shks=stat['shks'],
                sum_price=stat['sum_price']
            )

            if previous_stat:
                time_diff = (campaign_stat.date - previous_stat.date).total_seconds() / 60  # разница в минутах

                if time_diff > 0:
                    campaign_stat.views_per_minute = (float(campaign_stat.views) - float(previous_stat.views)) / time_diff
                    campaign_stat.clicks_per_minute = (float(campaign_stat.clicks) - float(previous_stat.clicks)) / time_diff
                    campaign_stat.sum_per_minute = (float(campaign_stat.sum) - float(previous_stat.sum)) / time_diff

            campaign_stat.save()

            for platform in stat['days'][0]['apps']:
                if platform['appType'] == 0: continue
                platform_stat = PlatformStatistic.objects.create(
                    campaign_statistic=campaign_stat,
                    app_type=platform['appType'],
                    views=platform['views'],
                    clicks=platform['clicks'],
                    ctr=platform['ctr'],
                    cpc=platform['cpc'],
                    sum=platform['sum'],
                    atbs=platform['atbs'],
                    orders=platform['orders'],
                    cr=platform['cr'],
                    shks=platform['shks'],
                    sum_price=platform['sum_price']
                )

                for product in platform['nm']:
                    ProductStatistic.objects.create(
                        platform_statistic=platform_stat,
                        nm_id=product['nmId'],
                        name=product['name'],
                        views=product['views'],
                        clicks=product['clicks'],
                        ctr=product['ctr'],
                        cpc=product['cpc'],
                        sum=product['sum'],
                        atbs=product['atbs'],
                        orders=product['orders'],
                        cr=product['cr'],
                        shks=product['shks'],
                        sum_price=product['sum_price']
                    )


def get_keyword_statistics(store, campaign_id):
    url = f'https://advert-api.wildberries.ru/adv/v1/stat/words?id={campaign_id}'
    headers = {
        'accept': 'application/json',
        'Authorization': store.wildberries_api_key,
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f'Error fetching keyword statistics: {response.json()} response.status: {response.status_code}')
        if response.status_code == 401:
            notify_wb(
                store.user,
                store.user,
                'Обновите API-ключ',
                'Мы не можем получить данные вашего магазина, потому что API-ключ Wildberries не принимается. Пожалуйста, обновите ключ в настройках магазина.',
                {'store_id': store.id}
            )
        return None


def save_keyword_statistics(store):
    campaigns = Campaign.objects.filter(
        store=store,
        type__in=[Campaign.Type.SEARCH, Campaign.Type.SEARCH_AND_CATALOG],
        status=Campaign.Status.ACTIVE
    )
    for campaign in campaigns:
        statistics = get_keyword_statistics(store, campaign.advert_id)

        if statistics and isinstance(statistics, dict) and 'words' in statistics:
            words_data = statistics['words']

            # Проверка на наличие нужных ключей в words_data
            required_keys = ['phrase', 'strong', 'excluded', 'pluse', 'fixed', 'keywords']
            if all(k in words_data for k in required_keys):
                KeywordData.objects.update_or_create(
                    campaign=campaign,
                    defaults={
                        'phrase': words_data['phrase'],
                        'strong': words_data['strong'],
                        'excluded': words_data['excluded'],
                        'pluse': words_data['pluse'],
                        'fixed': words_data['fixed'],
                    }
                )

                for keyword_stat in words_data['keywords']:
                    if isinstance(keyword_stat, dict) and 'keyword' in keyword_stat and 'count' in keyword_stat:
                        CampaignKeywordStatistic.objects.create(
                            campaign=campaign,
                            keyword=keyword_stat['keyword'],
                            count=keyword_stat['count'],
                            date_received=timezone.now()
                        )
                    else:
                        print(f"Пропущена некорректная запись ключевых слов: {keyword_stat}")
            else:
                print(f"Отсутствуют обязательные ключи в words_data: {words_data}")
        else:
            print(f"Неверная структура ответа от API или данные отсутствуют: {statistics}")


def get_auto_campaign_statistics(store, campaign_id):
    today = datetime.today().strftime('%Y-%m-%d')
    yesterday = (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d')
    url = (
        f'https://advert-api.wildberries.ru/adv/v0/stats/keywords'
        f'?advert_id={campaign_id}&from={yesterday}&to={today}'
    )

    headers = {
        'accept': 'application/json',
        'Authorization': store.wildberries_api_key,
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f'Error fetching auto campaign statistics: {response.json()}')
        if response.status_code == 401:
            notify_wb(
                store.user,
                store.user,
                'Обновите API-ключ',
                'Мы не можем получить данные вашего магазина, потому что API-ключ Wildberries не принимается. Пожалуйста, обновите ключ в настройках магазина.',
                {'store_id': store.id}
            )

        return None


def update_bid(campaign, new_bid):
    return True
    response = requests.post(
        'https://advert-api.wildberries.ru/adv/v0/cpm',
        headers={'Authorization': f'Bearer {campaign.store.wildberries_api_key}'},
        json={
            'advertId': campaign.id,
            'type': campaign.type,
            'cpm': new_bid,
            'param': campaign.united_params.subject.id,
            'instrument': 6
        }
    )
    return response


def save_auto_campaign_statistics(store):
    campaigns = Campaign.objects.filter(
        store=store,
        type=Campaign.Type.AUTO,
        status=Campaign.Status.ACTIVE
    )
    for campaign in campaigns:
        statistics = get_auto_campaign_statistics(store, campaign.advert_id)

        if statistics and isinstance(statistics, dict) and 'keywords' in statistics:
            for stat_item in statistics['keywords']:
                # Пример структуры: {"date": "2024-08-10", "stat": [{...}, {...}]}
                if isinstance(stat_item, dict) and 'date' in stat_item and 'stat' in stat_item:
                    date_recorded = stat_item['date']
                    for stat in stat_item['stat']:
                        AutoCampaignKeywordStatistic.objects.update_or_create(
                            campaign=campaign,
                            keyword=stat['keyword'],
                            date_recorded=date_recorded,
                            defaults={
                                'views': stat['views'],
                                'clicks': stat['clicks'],
                                'ctr': stat['ctr'],
                                'sum': stat['sum'],
                            }
                        )
                else:
                    print(f"Некорректный элемент в 'keywords': {stat_item}")
        else:
            print(f"Неверная структура ответа от API: {statistics}")
