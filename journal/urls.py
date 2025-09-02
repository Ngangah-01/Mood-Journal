from django.urls import path
from . import views 

urlpatterns = [ 
    path("", views.api_login, name="login"), 
    path("auth/login/", views.api_login, name="api_login"), 
    path("auth/register/", views.api_register, name="api_register"), 
    path("home/", views.home, name="home"), 
    path("api/journals/", views.api_journals, name="api_journals"),
    path("api/save/", views.api_save, name="api_save"),
    path("api/mood_trend/<str:period>/", views.mood_trend_view, name="mood_trend"), 
    path("api/pageAdd/", views.api_pageAdd, name="api_pageAdd"), 
    path("logout/", views.logout_view, name="logout"), 
    path("auth/logout/", views.api_logout, name="api_logout"), 
]