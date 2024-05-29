from django.shortcuts import render, redirect
from django.db.models import Q
from main.forms import *
from main.models import *
from main.consumers import allowManager

def homepage(request):
    send = {}
    token = request.GET["token"]
    send["userID"] = request.session[token]["userID"]
    send["token"] = token
    send["isManager"] = allowManager(request.session[token]["memberID"],request.session[token]["projectID"])
    send["memberID"] = request.session[token]["memberID"]
    participants = Participant.objects.filter(Id_member=request.session[token]["memberID"], Join=True)
    groupList = []
    for p in participants:
        groupList.append({"groupID":p.Id_group.pk,"GroupName":p.Id_group.GroupName,"participantID":p.pk})
    send["groupList"] = sorted(groupList, key=lambda x: x["GroupName"])

    return render(request, "group/homepage.html", send)

def backProject(request):
    token = request.GET["token"]
    return redirect(f"/project/homepage?token={token}")

def createGroup(request):
    send = {}
    token = request.GET["token"]
    send["userID"] = request.session[token]["userID"]
    send["token"] = token
    if request.method == "POST":
        form = CreateGroupForm(request.POST)
        if form.is_valid():
            newGroup = Group.objects.create(GroupName=form.cleaned_data["GroupName"])
            newGroup.save()
            member = Member.objects.get(Id_member=request.session[token]["memberID"])
            newParticipant = Participant.objects.create(Id_member=member, Id_group=newGroup, Position=TypeGroupPosition.TYPE0)
            newParticipant.save()
            return redirect(f"/group/homepage?token={token}")
        else:
            send["form"] = form
    else:
        send["form"] = CreateGroupForm()
    return render(request, "group/createGroup.html", send)

def editGroup(request, groupID):
    token = request.GET["token"]
    try:
        send = {}
        send["userID"] = request.session[token]["userID"]
        send["token"] = token
        send["groupID"] = groupID
        group = Group.objects.get(Id_group=groupID)
        lenGroup = len(Participant.objects.filter(Id_group=groupID, Join=True))
        if request.method == "POST":
            form = CreateGroupForm(request.POST)
            if form.is_valid():
                group.GroupName = form.cleaned_data["GroupName"]
                group.MaxNumber = form.cleaned_data["MaxNumber"]
                if group.MaxNumber >= lenGroup:
                    group.save()
                    return redirect(f"/group/homepage?token={token}")
                else:
                    send["form"] = form
                    send["mess"] = f"Nhóm có đang có số thành viên là: {lenGroup}. Cách chức bớt thành viên nếu bạn muốn có ít thành viên hơn."
            else:
                send["form"] = form
        else:
            send["form"] = CreateGroupForm(instance=group)
        return render(request, "group/editGroup.html", send)
    except:
        return redirect(f"/group/homepage?token={token}")


def editMemberGroup(request, groupID):
    token = request.GET["token"]
    try:
        send = {}
        send["userID"] = request.session[token]["userID"]
        send["token"] = token
        participants = Participant.objects.filter(Id_group=groupID, Join=True)
        send["groupID"] = groupID
        send["partID"] = Participant.objects.get(Id_member=request.session[token]["memberID"], Id_group=groupID, Join=True).pk
        sendPart = []
        for p in participants:
            isManager = False
            if p.Id_member.Position == "0": isManager = True
            state="Offline"
            if p.Id_member.Id_user.Online: state="Online"
            sendPart.append({"participantID":p.Id_participant,"avatar":p.Id_member.Id_user.Avatar.url,"name":p.Id_member.Id_user.Username,"position":p.Position,"online":state,"isManager":isManager})
        send["participants"] = sorted(sendPart, key = lambda x: x["name"])
        if request.method == "POST":
            searchStr = request.POST.get("searchStr")
            send["searchStr"] = searchStr
            memberInGroup = participants.values("Id_member")
            members = Member.objects.filter(Id_project=request.session[token]["projectID"]).exclude(Id_member__in=memberInGroup)
            members = members.filter(Q(Id_user__Id_user__icontains=searchStr) | Q(Id_user__Username__icontains=searchStr))
            sendMembers = []
            for member in members:
                state="Offline"
                if member.Id_user.Online: state="Online"
                sendMembers.append({"memberID":member.pk,"avatar":member.Id_user.Avatar.url,"name":member.Id_user.Username,"position":TypePosition.labels[int(member.Position)],"online":state})
            send["members"] = sendMembers
        return render(request, "group/editMemberGroup.html", send)
    except:
        return redirect(f"/group/homepage?token={token}")