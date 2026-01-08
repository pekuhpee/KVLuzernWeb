from django.urls import path
from apps.ranking import views

app_name = "ranking"
urlpatterns = [
    path("", views.start, name="start"),
    path("vote/", views.vote, name="vote"),
    path("results/", views.results, name="results"),
]
