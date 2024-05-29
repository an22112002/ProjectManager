from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path(r'ws/supportHandel/<str:support_id>', consumers.SupportHandel.as_asgi()),
    path(r'ws/onlineChecker/<str:user_id>', consumers.OnlineChecker.as_asgi()),
    path(r'ws/memberHandel/<str:member_id>/<str:project_id>', consumers.MemberHandel.as_asgi()),
    path(r'ws/participantHandel/<str:group_id>/<str:part_id>', consumers.ParticipantHandel.as_asgi()),
    path(r'ws/groupChatHandel/<str:member_id>/<str:group_id>/<str:participant_id>', consumers.GroupChatHandel.as_asgi()),
    path(r'ws/scheduleHandel', consumers.ScheduleHandel.as_asgi()),
    path(r'ws/getRepostHandel/<str:project_id>', consumers.GetRepostHandel.as_asgi()),
    path(r'ws/videoCallHandel/<str:type>/<str:id>/<str:memberID>', consumers.VideoCallHandel.as_asgi()),
]