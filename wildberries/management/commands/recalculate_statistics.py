from django.core.management.base import BaseCommand
from django.utils import timezone
from wildberries.models import CampaignStatistic
from datetime import timedelta

# python manage.py recalculate_statistics
#  sudo docker exec -it appseed_app python manage.py recalculate_statistics
class Command(BaseCommand):
    help = 'Recalculates views, clicks, and sum per minute for existing CampaignStatistic records'

    def handle(self, *args, **kwargs):
        # Получаем все кампании для пересчета статистики
        campaigns = CampaignStatistic.objects.values_list('campaign', flat=True).distinct()

        for campaign_id in campaigns:
            # Получаем все записи статистики для конкретной кампании в хронологическом порядке
            statistics = CampaignStatistic.objects.filter(campaign_id=campaign_id).order_by('date')

            previous_stat = None

            for stat in statistics:
                if previous_stat:
                    time_diff = (stat.date - previous_stat.date).total_seconds() / 60

                    if time_diff > 0:
                        stat.views_per_minute = (float(stat.views) - float(previous_stat.views)) / time_diff
                        stat.clicks_per_minute = (float(stat.clicks) - float(previous_stat.clicks)) / time_diff
                        stat.sum_per_minute = (float(stat.sum) - float(previous_stat.sum)) / time_diff

                    stat.save()

                previous_stat = stat

        self.stdout.write(self.style.SUCCESS('Successfully recalculated statistics for all campaigns.'))
