# wildberries/utils.py
from datetime import date

import requests
from .models import Store, Campaign, Subject, Menu, UnitedParam, CampaignStatistic, PlatformStatistic, ProductStatistic


def get_campaign_list(store):
    url = 'https://advert-api.wb.ru/adv/v1/promotion/count'
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
        return None

def get_campaign_details(store, advert_ids):
    url = 'https://advert-api.wb.ru/adv/v1/promotion/adverts?order=create&direction=asc'
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
        return None

def save_campaign_details(store, campaign_data):
    for campaign in campaign_data:
        if 'unitedParams' not in campaign:
            print('No unitedParams in loaded data. Not saved')
            continue

        advert_id = campaign['advertId']
        name = campaign['name']
        start_time = campaign['startTime']
        end_time = campaign['endTime']
        create_time = campaign['createTime']
        change_time = campaign['changeTime']
        search_pluse_state = campaign.get('searchPluseState', False)
        daily_budget = campaign['dailyBudget']
        status = campaign['status']
        type = campaign['type']
        payment_type = campaign['paymentType']

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

        for param in campaign['unitedParams']:
            catalog_cpm = param['catalogCPM']
            search_cpm = param['searchCPM']
            subject_data = param['subject']
            menus_data = param['menus']
            nms = param['nms']

            subject_obj, _ = Subject.objects.get_or_create(
                id=subject_data['id'],
                defaults={'name': subject_data['name']}
            )

            united_param_obj, _ = UnitedParam.objects.update_or_create(
                campaign=campaign_obj,
                subject=subject_obj,
                defaults={
                    'catalog_cpm': catalog_cpm,
                    'search_cpm': search_cpm,
                    'nms': nms
                }
            )

            for menu_data in menus_data:
                menu_obj, _ = Menu.objects.get_or_create(
                    id=menu_data['id'],
                    defaults={'name': menu_data['name']}
                )
                united_param_obj.menus.add(menu_obj)

def fetch_and_save_campaigns(store_id):
    try:
        print(f'Store with id {store_id} prepared to update')
        store = Store.objects.get(id=store_id)
        campaign_list_data = get_campaign_list(store)
        print(campaign_list_data)
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
    url = 'https://advert-api.wb.ru/adv/v2/fullstats'
    headers = {
        'accept': 'application/json',
        'Authorization': store.wildberries_api_key,
        'Content-Type': 'application/json'
    }
    response = requests.post(url, headers=headers, json=[{"id": advert_id} for advert_id in advert_ids])
    if response.status_code == 200:
        return response.json()
    else:
        print(f'Error fetching campaign statistics: {response.json()}')
        return None

def save_campaign_statistics(store):
    campaigns = Campaign.objects.filter(store=store)
    advert_ids = [campaign.advert_id for campaign in campaigns]
    statistics = get_campaign_statistics(store, advert_ids)
    if statistics:
        for stat in statistics:
            campaign = Campaign.objects.get(advert_id=stat['advertId'])
            campaign_stat, created = CampaignStatistic.objects.update_or_create(
                campaign=campaign,
                date=date.today(),
                defaults={
                    'views': stat['views'],
                    'clicks': stat['clicks'],
                    'ctr': stat['ctr'],
                    'cpc': stat['cpc'],
                    'sum': stat['sum'],
                    'atbs': stat['atbs'],
                    'orders': stat['orders'],
                    'cr': stat['cr'],
                    'shks': stat['shks'],
                    'sum_price': stat['sum_price']
                }
            )

            for platform in stat['days'][0]['apps']:
                platform_stat, created = PlatformStatistic.objects.update_or_create(
                    campaign_statistic=campaign_stat,
                    app_type=platform['appType'],
                    defaults={
                        'views': platform['views'],
                        'clicks': platform['clicks'],
                        'ctr': platform['ctr'],
                        'cpc': platform['cpc'],
                        'sum': platform['sum'],
                        'atbs': platform['atbs'],
                        'orders': platform['orders'],
                        'cr': platform['cr'],
                        'shks': platform['shks'],
                        'sum_price': platform['sum_price']
                    }
                )

                for product in platform['nm']:
                    ProductStatistic.objects.update_or_create(
                        platform_statistic=platform_stat,
                        nm_id=product['nmId'],
                        defaults={
                            'name': product['name'],
                            'views': product['views'],
                            'clicks': product['clicks'],
                            'ctr': product['ctr'],
                            'cpc': product['cpc'],
                            'sum': product['sum'],
                            'atbs': product['atbs'],
                            'orders': product['orders'],
                            'cr': product['cr'],
                            'shks': product['shks'],
                            'sum_price': product['sum_price']
                        }
                    )