from django.urls import path
from . import views

app_name = "alerts"
urlpatterns=[
    path("", views.index, name="index"),
    path("signup/", views.signup, name="signup"),
    path("login/", views.Login, name="login"),
    path("checkdata/",views.checkdata, name="checkdata"),
    path("logout/", views.Logout, name="logout"),
    path("alertmail/", views.alertmail, name="alertmail"),
]