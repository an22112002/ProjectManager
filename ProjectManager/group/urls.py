from django.urls import path
from . import views
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

urlpatterns = [
    path("homepage", views.homepage, name="homepage page"),
    path("backProject", views.backProject),
    path("createGroup", views.createGroup, name="create_group page"),
    path("editGroup/<str:groupID>", views.editGroup, name="edit_group page"),
    path("editMemberGroup/<str:groupID>", views.editMemberGroup, name="edit_member_group page"),
]

urlpatterns += staticfiles_urlpatterns()