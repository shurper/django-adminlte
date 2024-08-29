# wildberries/tasks.py
import logging
from datetime import timedelta

from celery import shared_task

from django.utils import timezone
import requests

logger = logging.getLogger('celery_tasks')


@shared_task
def fetch_and_save_campaigns(store_id):
    from .models import Store
    from .utils import get_campaign_list, get_campaign_details, save_campaign_details
    try:
        logger.info(f'Starting task for Store with id {store_id}')
        store = Store.objects.get(id=store_id, status="active")

        campaign_list_data = get_campaign_list(store)
        logger.debug(f'Campaign list data: {campaign_list_data}')

        if campaign_list_data and 'adverts' in campaign_list_data:
            logger.info(f'Fetched campaign list successfully for Store {store.name}')
            advert_ids = []
            for advert in campaign_list_data['adverts']:
                advert_ids.extend([item['advertId'] for item in advert['advert_list']])
            campaign_details_data = get_campaign_details(store, advert_ids)
            logger.debug(f'Campaign details data: {campaign_details_data}')

            if campaign_details_data:
                save_campaign_details(store, campaign_details_data)
                logger.info(f'Saved campaign details for Store {store.name}')
                # logger.info(f'Fetched data: {campaign_details_data}')
        else:
            logger.warning(f'No campaign data received or invalid format for Store {store.name}')
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
    from .utils import save_campaign_statistics
    active_stores = Store.objects.filter(status='active')
    for store in active_stores:
        save_campaign_statistics(store)


@shared_task
def collect_keyword_statistics():
    from .models import Store
    from .utils import save_keyword_statistics
    active_stores = Store.objects.filter(status='active')
    for store in active_stores:
        save_keyword_statistics(store)


@shared_task
def collect_auto_campaign_statistics():
    from .models import Store
    from .utils import save_auto_campaign_statistics
    active_stores = Store.objects.filter(status='active')
    for store in active_stores:
        save_auto_campaign_statistics(store)


@shared_task
def run_autobidder():
    print("run_autobidder is started")
    from .models import AutoBidderSettings, PositionTrackingTask
    from .utils import update_bid
    print("run_autobidder is started")
    now = timezone.now()
    autobidders = AutoBidderSettings.objects.filter(is_enabled=True)

    for autobidder in autobidders:
        print(f"Autobidder for {autobidder.campaign.name} is running.")

        if not is_within_schedule(autobidder, now):
            print(f"Autobidder for {autobidder.campaign.name} is not within schedule. Rejected.")
            continue

        # Try to retrieve an existing task in 'request' status
        task = PositionTrackingTask.objects.filter(
            campaign=autobidder.campaign,
        ).first()

        if task is None:
            # Create a new task if no 'request' status task exists
            task = PositionTrackingTask.objects.create(
                campaign=autobidder.campaign,
                product_id=autobidder.product_id,
                keyword=autobidder.keyword,
                destination=autobidder.destination,
                status='request',
                depth=autobidder.depth
            )
            print(f"New PositionTrackingTask created for {autobidder.campaign.name}.")
        else:
            print(f"Found existing PositionTrackingTask for {autobidder.campaign.name}.")

        if task.status != 'done':
            print(f"Autobidder for {autobidder.campaign.name} is waiting for the watcher to be completed. Rejected.")
            continue

        if task.actual_position is not None:
            new_bid = determine_new_bid(autobidder, task.actual_position)
            print(f"Autobidder for {autobidder.campaign.name} is going to set a new bid: {new_bid}.")
            print(f"Autobidder task data {task.watcher_data}")
            print(f"Autobidder task cpms {task.watcher_data.get('cpms', [])}")
            update_bid(autobidder, new_bid)
            from .models import AutoBidderLog
            AutoBidderLog.objects.create(
                campaign=autobidder.campaign,
                message=f"Position: {task.actual_position}, New Bid: {new_bid}",
                position=task.actual_position,
                bid=new_bid,
                product_id=task.product_id,
                destination=task.destination,
                depth=task.depth,
                keyword=task.keyword
                # position_delta=task.watcher_data.get('position_delta'),
                # product_price=task.watcher_data.get('product_price'),
                # average_cpm=task.watcher_data.get('average_cpm'),
                # cpm=task.watcher_data.get('cpm'),
                # before_average_cpm=task.watcher_data.get('before_average_cpm'),
                # min_cpm=task.watcher_data.get('min_cpm'),
                # before_min_cpm=task.watcher_data.get('before_min_cpm'),
                # max_cpm=task.watcher_data.get('max_cpm'),
                # before_max_cpm=task.watcher_data.get('before_max_cpm'),
                # average_advert_step_cost=task.watcher_data.get('average_advert_step_cost'),
                # before_average_advert_step_cost=task.watcher_data.get('before_average_advert_step_cost'),
                # advert_density=task.watcher_data.get('advert_density'),
                # advert_competitors_count=task.watcher_data.get('advert_competitors_count'),
                # advert_competitors_before=task.watcher_data.get('advert_competitors_before'),
                # advert_competitors_after=task.watcher_data.get('advert_competitors_after'),
                # advert_position=task.watcher_data.get('advert_position'),
                # advert_count=task.watcher_data.get('advert_count'),
                # cpms=task.watcher_data.get('cpms', []),
                # advert_step_costs=task.watcher_data.get('advert_step_costs', []),
                # advert_competitors=task.watcher_data.get('advert_competitors', []),
            )

        # Update task details
        task.product_id = autobidder.product_id
        task.keyword = autobidder.keyword
        task.destination = autobidder.destination
        task.depth = autobidder.depth
        task.status = 'request'
        task.save()


@shared_task
def run_monitoring():
    print("run_monitoring is started")
    from .models import AutoBidderSettings, PositionTrackingTask
    now = timezone.now()
    autobidders = AutoBidderSettings.objects.filter(is_enabled=True)

    for autobidder in autobidders:
        print(f"Monitoring for {autobidder.campaign.name} is running.")

        if not is_within_schedule(autobidder, now):
            print(f"Monitoring for {autobidder.campaign.name} is not within schedule. Rejected.")
            continue

        for keyword in autobidder.keywords_monitoring:
            for destination in autobidder.destinations_monitoring:
                # Try to retrieve an existing task in 'request' status
                task = PositionTrackingTask.objects.filter(
                    campaign=autobidder.campaign,
                    keyword=keyword,
                    destination=destination,
                ).first()

                if task is None:
                    # Create a new task if no 'request' status task exists
                    task = PositionTrackingTask.objects.create(
                        campaign=autobidder.campaign,
                        product_id=autobidder.product_id,
                        keyword=keyword,
                        destination=destination,
                        status='request',
                        depth=autobidder.depth
                    )
                    print(f"New PositionTrackingTask created for {autobidder.campaign.name} with keyword '{keyword}' and destination '{destination}'.")
                else:
                    print(f"Found existing PositionTrackingTask for {autobidder.campaign.name} with keyword '{keyword}' and destination '{destination}'.")

                if task.status != 'done':
                    print(f"Monitoring for {autobidder.campaign.name} is waiting for the watcher to be completed. Rejected.")
                    continue

                if task.actual_position is not None:
                    from .models import AutoBidderLog
                    AutoBidderLog.objects.create(
                        campaign=autobidder.campaign,
                        message=f"Position: {task.actual_position}",
                        position=task.actual_position,
                        bid=0,
                        product_id=task.product_id,
                        destination=task.destination,
                        depth=task.depth,
                        keyword=task.keyword,
                        position_delta=task.watcher_data.get('position_delta'),
                        product_price=task.watcher_data.get('product_price'),
                        average_cpm=task.watcher_data.get('average_cpm'),
                        cpm=task.watcher_data.get('cpm'),
                        before_average_cpm=task.watcher_data.get('before_average_cpm'),
                        min_cpm=task.watcher_data.get('min_cpm'),
                        before_min_cpm=task.watcher_data.get('before_min_cpm'),
                        max_cpm=task.watcher_data.get('max_cpm'),
                        before_max_cpm=task.watcher_data.get('before_max_cpm'),
                        average_advert_step_cost=task.watcher_data.get('average_advert_step_cost'),
                        before_average_advert_step_cost=task.watcher_data.get('before_average_advert_step_cost'),
                        advert_density=task.watcher_data.get('advert_density'),
                        advert_competitors_count=task.watcher_data.get('advert_competitors_count'),
                        advert_competitors_before=task.watcher_data.get('advert_competitors_before'),
                        advert_competitors_after=task.watcher_data.get('advert_competitors_after'),
                        advert_position=task.watcher_data.get('advert_position'),
                        advert_count=task.watcher_data.get('advert_count'),
                        cpms=task.watcher_data.get('cpms', []),
                        advert_step_costs=task.watcher_data.get('advert_step_costs', []),
                        advert_competitors=task.watcher_data.get('advert_competitors', []),
                    )

                # Update task details
                task.product_id = autobidder.product_id
                task.keyword = keyword
                task.destination = destination
                task.depth = autobidder.depth
                task.status = 'request'
                task.save()


def is_within_schedule(autobidder, now):
    return True
    weekly_schedule = autobidder.weekly_schedule or []
    intra_day_schedule = autobidder.intra_day_schedule or []
    if now.strftime('%A') not in weekly_schedule:
        return False
    for period in intra_day_schedule:
        start = timezone.datetime.strptime(period['start'], '%H:%M').time()
        end = timezone.datetime.strptime(period['end'], '%H:%M').time()
        if start <= now.time() <= end:
            return False
    return True


def determine_new_bid(autobidder, position):
    # Получаем все объекты PositionRange для данного autobidder
    position_ranges = autobidder.position_ranges.all()

    # Проходимся по каждому диапазону
    for range_obj in position_ranges:
        start = range_obj.start_position
        end = range_obj.end_position
        bid = range_obj.bid

        # Проверяем, входит ли текущая позиция в данный диапазон
        if start <= position <= end:
            print(f"New bid is {bid}")
            return bid

    # Если позиция не попадает ни в один из диапазонов, возвращаем 0
    return 0


@shared_task
def delete_stale_tasks():
    from .models import PositionTrackingTask
    # Определяем время, более которого задачи считаются "зависшими"
    stale_time = timezone.now() - timedelta(minutes=10)
    print(f"delete_stale_tasks. stale_time: {stale_time}")
    # Находим и удаляем задачи со статусом "in_progress", обновленные более 10 минут назад
    stale_tasks = PositionTrackingTask.objects.filter(status='in_progress', updated_at__lt=stale_time)
    count = stale_tasks.count()
    stale_tasks.delete()

    return f'{count} stale tasks deleted'