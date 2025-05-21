# wildberries/urls.py
from django.urls import path, include
from . import views
from .views import edit_store, autobidder_view, observer_get_task, observer_report_position, api_get_chart_data, \
    api_get_destinations, api_get_products, api_get_stat_chart_data, monitoring_view, monitoring_additional_words_view, \
    keywords_monitoring_view, api_get_chart_data_keywords

urlpatterns = [
    path('', views.index, name='index'),
    path('stores/', views.stores, name='stores'),
    path('stores/add/', views.add_store, name='add_store'),
    path('stores/edit/<int:pk>/', edit_store, name='edit_store'),
    path('stores/<int:store_id>/campaigns/', views.store_campaigns, name='store_campaigns'),
    path('store/<int:store_id>/update_campaigns/', views.update_campaigns, name='update_campaigns'),
    path('campaigns/<int:campaign_id>/', views.campaign_detail, name='campaign_detail'),
    path('platform_statistics/<int:campaign_statistic_id>/', views.platform_statistic_detail, name='platform_statistic_detail'),
    path('product_statistics/<int:platform_statistic_id>/', views.product_statistic_detail, name='product_statistic_detail'),
    path('keyword_statistics/<int:campaign_id>/', views.keyword_statistics, name='keyword_statistics'),
    path('auto_keyword_statistics/<int:campaign_id>/', views.auto_keyword_statistics, name='auto_keyword_statistics'),
    path('autobidder/<int:campaign_id>/', autobidder_view, name='autobidder_view'),
    path('monitoring/<int:campaign_id>/', monitoring_view, name='monitoring_view'),
    path('monitoring/additional_words/<int:campaign_id>/', monitoring_additional_words_view, name='monitoring_additional_words_view'),
    path('monitoring/keywords_monitoring/<int:campaign_id>/', keywords_monitoring_view, name='keywords_monitoring_view'),

    path('api/observer/task/', observer_get_task, name='observer_get_task'),
    path('api/observer/report/', observer_report_position, name='observer_report_position'),
    path('api/chart-data/', api_get_chart_data, name='api_get_chart_data'),
    path('api/chart-data-keywords/', api_get_chart_data_keywords, name='api_get_chart_data_keywords'),
    path('api/stat-data/', api_get_stat_chart_data, name='api_get_stat_chart_data'),
    path('api/destinations/', api_get_destinations, name='api_get_destinations'),
    path('api/products/', api_get_products, name='api_get_products'),
    #path('store/<int:store_id>/store_campaigns/', views.store_campaigns, name='store_campaigns'),
   # path('campaign_list', views.campaign_list, name='campaign_list'),
]
