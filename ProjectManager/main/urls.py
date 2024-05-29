from django.urls import path
from . import views
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

urlpatterns = [
    path("test", views.test, name="test page"),
    path("login", views.login, name="login page"),
    path("signup", views.signup, name="signup page"),
    path("logout", views.logout, name="logout"),
    path("support/<str:position>/<str:supportID>", views.support, name="support page"),
    path("homepage", views.homepage, name="main_homepage page"),
    path("createProject", views.createProject, name="create_project page"),
    path("changePass", views.changePass, name="change_password page"),
    path("editAccount", views.editAccount, name="edit_account page"),
    path("projectHomepage/<str:projectID>/<str:memberID>", views.projectHomepage, name="project_homepage page"),
    path("videoCall", views.videoCall, name="video_call page"),
]

urlpatterns += staticfiles_urlpatterns()