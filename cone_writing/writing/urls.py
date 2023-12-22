# -*- coding:utf-8 -*-

# author: Cone
# datetime: 2021-02-22 17:32
# software: PyCharm

from django.urls import path
from rest_framework.routers import DefaultRouter
from . import views

tag_router = DefaultRouter()
tag_router.register('tag', viewset=views.TagViewSet)

media_router = DefaultRouter()
media_router.register('media', viewset=views.MediaViewSet)


urlpatterns = [
    path('search/', views.SearchView.as_view()),
    path('moment/group/', views.MomentViewSet.group),
    path('storage/token/', views.QiNiuStorageView.get_upload_token),
    path('moment/', views.MomentViewSet.as_view({
        'get': 'list',
        'post': 'create',
        'delete': 'destroy'
    })),
] + tag_router.urls + media_router.urls
