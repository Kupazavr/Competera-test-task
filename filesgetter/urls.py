from django.urls import path, include
from django.conf.urls import url
from . import views

urlpatterns = [
    #path('1/', views.index),
    path('2/', views.templateview),
    path('3/', views.uploader),
]
