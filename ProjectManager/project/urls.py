from django.urls import path
from . import views
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

urlpatterns = [
    path("homepage", views.homepage, name="project_homepage page"),
    path("backMain", views.backMain),
    path("editProject", views.editProject, name="edit_project page"),
    path("schedule", views.schedule, name="schedule page"),
    path("makeRepost/<str:assignID>", views.makeRepost, name="make_repost page"),
    path("readRepost/<str:repostID>", views.readRepost, name="read_repost page"),
    path("readCheck/<str:checkID>", views.readCheck, name="read_check page"),
    path("deleteRepost/<str:type>/<str:ID>/<str:token>", views.deleteRepost),
    path("readProjectRepost/<str:repostID>", views.readProjectRepost, name="read_project_repost page"),
    path("setProgress/<str:taskID>", views.setProgress, name="set_progress page"),
    path("editMember", views.editMember, name="edit_member page"),
    path("addMember", views.addMember, name="add_member page"),
    path("makeProjectRepost", views.makeProjectRepost, name="make_project_repost page"),
    path("showProgress", views.showProgress, name="show_progress page"),
    path("sharingFile", views.sharingFile, name="sharing_file page"),
    path("finishProject", views.finishProject, name="finish_project page"),
    path("summaryProject/<str:projectID>", views.summaryProject, name="summary_project page"),
    path("downloadFile/", views.downloadFile),
    path("watchFile/", views.watchFile),
    path("deleteFile/", views.deleteFile),
    path("setAllowFinish/<str:agree>/<str:token>", views.setAllowFinish),
    path("groupHomepage", views.groupHomepage, name="group_homepage page"),
    path("videoCall", views.videoCall, name="video_call page"),
]

urlpatterns += staticfiles_urlpatterns()