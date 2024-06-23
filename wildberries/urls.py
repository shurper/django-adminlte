# wildberries/urls.py
from django.urls import path
from . import views
from .views import edit_store

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
    #path('store/<int:store_id>/store_campaigns/', views.store_campaigns, name='store_campaigns'),
   # path('campaign_list', views.campaign_list, name='campaign_list'),
]
