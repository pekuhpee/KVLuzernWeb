from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("pruefungen", views.pruefungen, name="pruefungen"),
    path("starter/", views.starter, name="starter"),
]
