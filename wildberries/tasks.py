# wildberries/tasks.py
import logging

from celery import shared_task

from .utils import get_campaign_list, get_campaign_details, save_campaign_details, save_campaign_statistics

logger = logging.getLogger('celery_tasks')

@shared_task
def fetch_and_save_campaigns(store_id):
    from .models import Store
    try:
        logger.info(f'Starting task for Store with id {store_id}')
        store = Store.objects.get(id=store_id, status="active")
        campaign_list_data = get_campaign_list(store)
        if campaign_list_data:
            logger.info(f'Fetched campaign list successfully for Store {store.name}')
            advert_ids = []
            for advert in campaign_list_data['adverts']:
                advert_ids.extend([item['advertId'] for item in advert['advert_list']])
            campaign_details_data = get_campaign_details(store, advert_ids)
            if campaign_details_data:
                save_campaign_details(store, campaign_details_data)
                logger.info(f'Saved campaign details for Store {store.name}')
        else:
            logger.warning(f'No campaign data received for Store {store.name}')
    except Store.DoesNotExist:
        logger.error(f'Store with id {store_id} does not exist')


@shared_task
def update_all_stores_campaigns():
    from .models import Store
    active_stores = Store.objects.filter(status="active")
    for store in active_stores:
        store.update_campaigns()


@shared_task
def collect_campaign_statistics():
    from .models import Store
    active_stores = Store.objects.filter(status='active')
    for store in active_stores:
        save_campaign_statistics(store)