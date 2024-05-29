from django.shortcuts import render, redirect, HttpResponse
from django.db.models import Q
from main.forms import *
from main.models import *
from main.supposter import *
from reportlab.pdfgen import canvas
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from PIL import Image
from docx import Document
import os, datetime, io

def allowToEditProgress(taskID, memberID):
    member = Member.objects.get(Id_member=memberID)
    if member.Position == "0": return True
    try:
        assign = Assign.objects.get(Id_task=taskID)
        if assign.Id_group == "":
            return False
        else:
            captain = Participant.objects.get(Id_group=assign.Id_group,Position="0")
            if captain.Id_member == memberID:
                return True
            else:
                return False
    except Assign.DoesNotExist:
        return False
    except Participant.DoesNotExist:
        return False

def descripProgress(project):
    respone = ""
    phases = Phase.objects.filter(Id_project=project).order_by("Order")
    for phase in phases:
        tasks = Task.objects.filter(Id_phase=phase.Id_phase).order_by("Order")
        if len(tasks)!=0:
            budgetPhase = sum(task.Budget for task in tasks)
            progressPhase = round(sum(task.Progress for task in tasks)/len(tasks))
        else:
            budgetPhase = 0
            progressPhase = 0
        respone += f"\nGiai đoạn:{phase.PhaseName};Chi phí:{budgetPhase};Tiến độ:{progressPhase}%"
        for task in tasks:
            budgetTask = task.Budget
            progressTask = task.Progress
            respone += f"\nNhiệm vụ:{task.TaskName};Chi phí:{budgetTask};Tiến độ:{progressTask}%"
    return respone

def getProgress(project):
    respone = []
    sumBudget = 0
    today = datetime.datetime.now().date()
    phases = Phase.objects.filter(Id_project=project).order_by("Order")
    for phase in phases:
        tasks = Task.objects.filter(Id_phase=phase.Id_phase).order_by("Order")
        if len(tasks)!=0:
            progressPhase = round(sum(task.Progress for task in tasks)/len(tasks))
        else:
            progressPhase = 0
        respone.append({'Type':'Phase','Name':phase.PhaseName,'Progress':progressPhase, 'Status':getStatus(today, phase.StartDate, phase.EndDate, progressPhase)})
        for task in tasks:
            sumBudget += task.Budget
            respone.append({'Type':'Task','Name':task.TaskName,'Progress':task.Progress, 'Status':getStatus(today, task.StartDate, task.EndDate, task.Progress)})
    return respone, sumBudget

def resetAgree(projectID):
    members = Member.objects.filter(Q(Id_project=projectID) & Q(Position="2"))
    for m in members:
        m.AllowFinish = False

def isNotAllowToEdit(projectID):
    project = Project.objects.get(Id_project=projectID)
    return project.Finished

def canFinishProject(projectID):
    phases = Phase.objects.filter(Id_project=projectID)
    for phase in phases:
        tasks = Task.objects.filter(Id_phase=phase.pk)
        # giai đoạn nào cũng phải có nhiệm vụ
        if len(tasks) == 0:
            return False
        for task in tasks:
            try:
                assign = Assign.objects.get(Id_task=task.pk)
                reposts = Repost.objects.filter(Id_assign=assign.pk)
                # tất cả nhiệm vụ phải có báo cáo và tiến độ 100%
                if task.Progress != 100 and len(reposts) > 0:
                    resetAgree(projectID)
                    return False
            except: 
                return False
    return True

def checkClientAgree(projectID):
    members = Member.objects.filter(Q(Id_project=projectID) & Q(Position="2"))
    for m in members:
        if m.AllowFinish == False:
            return False
    return True

def getGroupsJoin(member):
    result = ""
    participants = Participant.objects.filter(Id_member=member.pk)
    for p in participants:
        result += f"{p.Id_group.GroupName}, "
    if result != "":
        return result[0:len(result)-2]
    else:
        return "Không tham gia nhóm nào"

def getAssignTask(member):
    result = ""
    reposts = Repost.objects.filter(Id_writer=member.pk)
    for r in reposts:
        result += f"{r.Id_assign.Id_task.TaskName}, "
    if result != "":
        return result[0:len(result)-2]
    else:
        return "Không thực hiện nhiệm vụ nào"

def getMissionRealDate(id, type):
    if type=="phase":
        tasks = Task.objects.filter(Id_phase=id)
        dates = []
        for task in tasks:
            b, e = getMissionRealDate(task.pk, "task")
            dates += [b, e]
        return min(dates), max(dates)
    else:
        assign = Assign.objects.get(Id_task=id)
        reposts = Repost.objects.filter(Id_assign=assign.pk).order_by("RealStartDate")
        return reposts.first().RealStartDate, reposts.last().DateRepost.date()

def homepage(request):
    send = {}
    token = request.GET["token"]
    send["userID"] = request.session[token]["userID"]
    send["token"]= token
    projectID = request.session[token]["projectID"]
    project = Project.objects.get(Id_project=projectID)
    send["project"] = project
    me = Member.objects.get(Id_member=request.session[token]["memberID"])
    today = datetime.datetime.now().date()
    assign = Assign.objects.filter(Id_member=me)
    unfinishTask = []
    for a in assign:
        if a.Id_task.Progress < 100:
            unfinishTask.append({"NameTask":a.Id_task.TaskName,"Status":getStatus(today, a.Id_task.StartDate, a.Id_task.EndDate, a.Id_task.Progress)})
    unfinishTask = reorderTask(unfinishTask)
    if len(unfinishTask) != 0:
        send["unfinishTasks"] = unfinishTask
    # kiểm tra có thể kết thúc dự án ko
    canFinish = canFinishProject(projectID)
    send["canFinish"] = canFinish
    # phân quyền người dùng
    if me.Position == "0":
        send["isManager"] = True
        if canFinish and checkClientAgree(projectID):
            send["allAgree"] = True
    else:
        send["isManager"] = False
    if me.Position == "2":
        send["isClient"] = True
        if canFinish:
            send["clientAgree"] = me.AllowFinish
    else:
        send["isClient"] = False
    return render(request, "project/homepage.html", send)

def backMain(request):
    token = request.GET["token"]
    return redirect(f"/main/homepage?token={token}")

def editProject(request):
    send = {}
    token = request.GET["token"]
    send["userID"] = request.session[token]["userID"]
    send["token"] = token
    if isNotAllowToEdit(request.session[token]["projectID"]):
        return redirect(f"/main/homepage?token={token}")
    user = User.objects.get(Id_user=request.session[token]["userID"])
    project = Project.objects.get(Id_project=request.session[token]["projectID"])
    choices = Member.objects.filter(Id_project=project).exclude(Position="2")
    me = choices.get(Id_user=user)
    if request.method == "POST":
        form = EditProjectForm(request.POST,choices=choices,old=me)
        if form.is_valid():
            newManagerID = request.POST.get("managerChoice")
            project.NameProject = request.POST.get("NameProject")
            project.Description = request.POST.get("Description")
            project.Budget = request.POST.get("Budget")
            project.save()
            if newManagerID != me.Id_member:
                me.Position = TypePosition.TYPE1
                newManager = choices.get(Id_member=newManagerID)
                newManager.Position = TypePosition.TYPE0
                me.save()
                newManager.save()
            return redirect(f"/project/homepage?token={token}")
        send["form"] = form
    else:
        send["form"] = EditProjectForm(instance=project,choices=choices,old=me)
    return render(request, "project/editProject.html", send)

def schedule(request):
    send = {}
    token = request.GET["token"]
    send["userID"] = request.session[token]["userID"]
    send["token"] = token
    if isNotAllowToEdit(request.session[token]["projectID"]):
        return redirect(f"/main/homepage?token={token}")
    me = Member.objects.get(Id_member=request.session[token]["memberID"])
    send["pos"] = me.Position
    send["memberID"] = me.Id_member
    project = Project.objects.get(Id_project=request.session[token]["projectID"])
    send["projectID"] = project.Id_project
    send["today"] = datetime.datetime.today().strftime("%Y-%m-%d")
    # lấy dữ liệu
    phases = Phase.objects.filter(Id_project=request.session[token]["projectID"]).order_by("Order")
    missions = []
    i = 0
    for phase in phases:
        tasks = Task.objects.filter(Id_phase=phase.Id_phase).order_by("Order")
        if len(tasks)!=0:
            budget = sum(task.Budget for task in tasks)
            progress = round(sum(task.Progress for task in tasks)/len(tasks))
        else:
            budget = 0
            progress = 0
        missions.append({
            "type":"phase",
            "Name":phase.PhaseName,
            "Order":phase.Order,
            "Budget":budget,
            "Progress":progress,
            "StartDate":phase.StartDate.strftime("%d/%m"),
            "EndDate":phase.EndDate.strftime("%d/%m"),
            "FullStartDate":phase.StartDate.strftime("%Y-%m-%d"),
            "FullEndDate":phase.EndDate.strftime("%Y-%m-%d"),
            "id":str(i),
            "ID":phase.Id_phase,
        })
        i += 1
        for task in tasks:
            try:
                assign = Assign.objects.get(Id_task=task)
                assigner = assign.Id_member.Id_user.Username
            except Assign.DoesNotExist:
                assign = None
                assigner = "Chưa phân công"
            missions.append({
                "type":"task",
                "Name":task.TaskName,
                "Order":task.Order,
                "Budget":task.Budget,
                "Progress":task.Progress,
                "Description":task.Description,
                "StartDate":task.StartDate.strftime("%d/%m"),
                "EndDate":task.EndDate.strftime("%d/%m"),
                "FullStartDate":task.StartDate.strftime("%Y-%m-%d"),
                "FullEndDate":task.EndDate.strftime("%Y-%m-%d"),
                "id":str(i),
                "ID":task.Id_task,
                "Assign":assign,
                "Assigner":assigner
            })
            i += 1
    send["missions"] = missions
    # tạo danh sách ngày
    if phases:
        dates = []
        for phase in phases:
            dates.append(phase.StartDate)
            dates.append(phase.EndDate)
        send["arrDates"], send["arrDatesLimit"], send["lenArr"] = arrayDates(min(dates), max(dates))
    # form
    send["formPhase"] = MakePhaseForm()
    send["formTask"] = MakeTaskForm()
    # assign form info
    members = Member.objects.filter(Id_project=project.pk).exclude(Position="2")
    p = Participant.objects.filter(Id_member__in=members)
    send["groupsAssignForm"] = Group.objects.filter(Id_group__in=p.values("Id_group"))
    return render(request, "project/schedule.html", send)

def makeRepost(request, assignID):
    send = {}
    token = request.GET["token"]
    send["userID"] = request.session[token]["userID"]
    send["token"] = token
    if isNotAllowToEdit(request.session[token]["projectID"]):
        return redirect(f"/main/homepage?token={token}")
    if request.method == "POST":
        form = MakeRepostForm(request.POST)
        if form.is_valid() and form.is_dateCorrect():
            newRepost = Repost.objects.create(
                Id_assign = Assign.objects.get(Id_assign=assignID),
                Id_writer = Member.objects.get(Id_member=request.session[token]["memberID"]),
                Description = form.cleaned_data["Description"],
                Result = form.cleaned_data["Result"],
                RealStartDate = form.cleaned_data["RealStartDate"]
            )
            newRepost.save()
            return redirect(f"/project/schedule?token={token}")
        else:
            send["form"] = form
            if not form.is_valid():
                send["mess"] = "Nhập đầy đủ thông tin"
            elif not form.is_dateCorrect():
                send["mess"] = "Ngày bắt đầu không thể sau ngày báo cáo"
    else:
        send["form"] = MakeRepostForm()
    return render(request, "project/makeRepost.html", send)

def readRepost(request, repostID):
    send = {}
    token = request.GET["token"]
    send["userID"] = request.session[token]["userID"]
    send["allowDel"] = False
    print(Member.objects.get(Id_member=request.session[token]["memberID"]).Position == "0")
    print(Project.objects.get(Id_project=request.session[token]["projectID"]).Finished == False)
    print(request.session[token]["projectID"])
    if Member.objects.get(Id_member=request.session[token]["memberID"]).Position == "0" and Project.objects.get(Id_project=request.session[token]["projectID"]).Finished == False:
        send["allowDel"] = True
    send["token"] = token
    send["type"] = "R"
    send["ID"] = repostID
    repost = Repost.objects.get(Id_repost=repostID)
    send["form"] = ShowRepostForm(instance=repost)
    return render(request, "project/readRepost.html", send)

def readCheck(request, checkID):
    send = {}
    token = request.GET["token"]
    send["userID"] = request.session[token]["userID"]
    send["allowDel"] = False
    if Member.objects.get(Id_member=request.session[token]["memberID"]).Position == "0" and Project.objects.get(Id_project=request.session[token]["projectID"]).Finished == False:
        send["allowDel"] = True
    send["token"] = token
    send["type"] = "C"
    send["ID"] = checkID
    check = Check.objects.get(Id_check=checkID)
    send["form"] = ReadCheckForm(instance=check)
    return render(request, "project/readRepost.html", send)

def readProjectRepost(request, repostID):
    send = {}
    token = request.GET["token"]
    send["userID"] = request.session[token]["userID"]
    send["allowDel"] = False
    if Member.objects.get(Id_member=request.session[token]["memberID"]).Position == "0" and Project.objects.get(Id_project=request.session[token]["projectID"]).Finished == False:
        send["allowDel"] = True
    send["token"] = token
    send["type"] = "PR"
    send["ID"] = repostID
    projectRepost = ProjectRepost.objects.get(Id_repost=repostID)
    send["form"] = ReadProjectRepostForm(instance=projectRepost)
    send["readPR"] = True
    return render(request, "project/readRepost.html", send)

def deleteRepost(request, type, ID, token):
    if isNotAllowToEdit(request.session[token]["projectID"]):
        return redirect(f"/main/homepage?token={token}")
    if type == "R":
        try:
            repost = Repost.objects.get(Id_repost=ID)
            repost.delete()
        except:
            pass
        return redirect(f"/project/schedule?token={token}")
    elif type == "PR":
        try:
            repost = ProjectRepost.objects.get(Id_repost=ID)
            repost.delete()
        except:
            pass
        return redirect(f"/project/showProgress?token={token}")
    elif type == "C":
        try:
            check = Check.objects.get(Id_check=ID)
            allCheck = Check.objects.filter(Id_assign=check.Id_assign).order_by("-DateCheck")
            if allCheck[0].Id_check == check.Id_check:
                task = Task.objects.get(Id_task=check.Id_assign.Id_task.pk)
                if len(allCheck) == 1:
                    task.Progress = 0
                else:
                    task.Progress = allCheck[1].Progress
                task.save()
            check.delete()
        except Exception as e:
            print(e)
        return redirect(f"/project/schedule?token={token}")
    return redirect(f"/project/homepage?token={token}")

def setProgress(request, taskID):
    send = {}
    token = request.GET["token"]
    if isNotAllowToEdit(request.session[token]["projectID"]):
        return redirect(f"/main/homepage?token={token}")
    send["userID"] = request.session[token]["userID"]
    send["token"] = token
    try:
        task = Task.objects.get(Id_task=taskID)
        assign = Assign.objects.get(Id_task=taskID)
        if allowToEditProgress(taskID, request.session[token]["memberID"]):
            send["editable"] = True
            send["form"] = MakeCheckForm()
        else:
            send["editable"] = False
        if request.method == "POST":
            progress = request.POST.get("progress")
            task.Progress = progress
            task.save()
            form = MakeCheckForm(request.POST)
            if form.is_valid():
                member = Member.objects.get(Id_member = request.session[token]["memberID"])
                check = Check.objects.create(Id_assign = assign, Id_writer = member, Result = form.cleaned_data["Result"],Progress = progress)
                check.save()
            else:
                send["form"] = form
        try:
            reposts = Repost.objects.filter(Id_assign=assign).order_by("-DateRepost")
            sendRepost = []
            for r in reposts:
                sendRepost.append({"repostID":r.Id_repost, "DateRepost":r.DateRepost.strftime("%Y-%m-%d, %I:%M %p")})
            send["reposts"] = sendRepost
            send["lenReposts"] = len(sendRepost)
        except Assign.DoesNotExist:
            pass
        try:
            checks = Check.objects.filter(Id_assign=assign).order_by("-DateCheck")
            sendCheck = []
            for c in checks:
                sendCheck.append({"checkID":c.Id_check, "DateCheck":c.DateCheck.strftime("%Y-%m-%d, %I:%M %p")})
            send["checks"] = sendCheck
            send["lenChecks"] = len(sendCheck)
        except Check.DoesNotExist:
            pass
        send["progress"] = task.Progress
        return render(request, "project/setProgress.html", send)
    except:
        return redirect(f"/project/schedule?token={token}")

def editMember(request):
    send = {}
    token = request.GET["token"]
    if isNotAllowToEdit(request.session[token]["projectID"]):
        return redirect(f"/main/homepage?token={token}")
    send["userID"] = request.session[token]["userID"]
    send["token"] = token
    send["memberID"] = request.session[token]["memberID"]
    send["projectID"] = request.session[token]["projectID"]
    members = Member.objects.filter(Id_project=request.session[token]["projectID"]).order_by("Id_user")
    sendMembers = []
    for member in members:
        state="Offline"
        if member.Id_user.Online: state="Online"
        allow="Không đồng ý"
        if member.AllowFinish: allow="Đồng ý"
        sendMembers.append({"id_member":member.Id_member, "avatar":member.Id_user.Avatar.url, "username":member.Id_user.Username, "position":TypePosition.labels[int(member.Position)], "email":member.Id_user.Email, "online":state, "allow":allow})
    sendMembers = sorted(sendMembers, key=lambda x: x['username'])
    send["sendMembers"] = sendMembers
    me = Member.objects.get(Id_member=request.session[token]["memberID"])
    if me.Position == "0":
        send["isManager"] = True
    else:
        send["isManager"] = False
    return render(request, "project/editMember.html", send)

def addMember(request):
    send = {}
    token = request.GET["token"]
    if isNotAllowToEdit(request.session[token]["projectID"]):
        return redirect(f"/main/homepage?token={token}")
    send["userID"] = request.session[token]["userID"]
    send["token"] = token
    send["memberID"] = request.session[token]["memberID"]
    send["projectID"] = request.session[token]["projectID"]
    if request.method == "POST":
        searchStr = request.POST.get("searchStr")
        send["searchStr"] = searchStr
        inProject = Member.objects.filter(Id_project=Project.objects.get(Id_project=request.session[token]["projectID"])).values('Id_user')
        users = User.objects.filter(Q(Id_user__icontains=searchStr) | Q(Username__icontains=searchStr) | Q(Email__icontains=searchStr)).exclude(Id_user__in=inProject).order_by("Username")
        sendUsers = []
        for user in users:
            state="Offline"
            if user.Online: state="Online"
            sendUsers.append({"id_user":user.Id_user, "avatar":user.Avatar.url, "username":user.Username, "typeUser":TypeUsers.labels[int(user.TypeUser)], "email":user.Email, "online":state})
        send["users"] = sendUsers
    return render(request, "project/addMember.html", send)

def makeProjectRepost(request):
    send = {}
    token = request.GET["token"]
    if isNotAllowToEdit(request.session[token]["projectID"]):
        return redirect(f"/main/homepage?token={token}")
    send["userID"] = request.session[token]["userID"]
    send["token"] = token
    if request.method == "POST":
        form = MakeProjectRepostForm(request.POST)
        print(request.POST.get("Risk"))
        print(request.POST.get("Progress"))
        if form.is_valid():
            print("valid")
            p = Project.objects.get(Id_project=request.session[token]["projectID"])
            print("make")
            newProjectRepost = ProjectRepost.objects.create(
                Id_project = p,
                Progress = form.cleaned_data["Progress"],
                Risk = form.cleaned_data["Risk"],
                Propose = form.cleaned_data["Propose"],
            )
            newProjectRepost.save()
            return redirect(f"/project/homepage?token={token}")
        else:
            send["form"] = form
    else:
        print("start")
        project = Project.objects.get(Id_project=request.session[token]["projectID"])
        respone = descripProgress(project)
        send["form"] = MakeProjectRepostForm(initial={"Progress":respone})
    return render(request, "project/makeProjectRepost.html", send)

def showProgress(request):
    send = {}
    token = request.GET["token"]
    if isNotAllowToEdit(request.session[token]["projectID"]):
        return redirect(f"/main/homepage?token={token}")
    send["userID"] = request.session[token]["userID"]
    send["token"] = token
    project = Project.objects.get(Id_project=request.session[token]["projectID"])
    progress, sumBudget = getProgress(project)
    send["budget"] = project.Budget
    send["budgetUsed"] = sumBudget
    send["budgetNotUse"] = project.Budget - sumBudget
    send["progress"] = progress
    projectReposts = ProjectRepost.objects.filter(Id_project=project).order_by("-DateRepost")
    sendReposts = []
    for pr in projectReposts:
        sendReposts.append({"id":pr.Id_repost,"date":pr.DateRepost.strftime("%Y-%m-%d, %I:%M %p")})
    send["reposts"] = sendReposts
    send["lenRepost"] = len(sendReposts)
    return render(request, "project/showProgress.html", send)

def sharingFile(request):
    send = {}
    token = request.GET["token"]
    if isNotAllowToEdit(request.session[token]["projectID"]):
        return redirect(f"/main/homepage?token={token}")
    send["userID"] = request.session[token]["userID"]
    send["position"] = Member.objects.get(Id_member=request.session[token]["memberID"]).Position
    send["token"] = token
    if request.method == "POST" and request.FILES:
        uploaded_file = request.FILES['file']
        if uploaded_file.size <= 5242880:
            newFile = SharingFile.objects.create(
                Id_project=Project.objects.get(Id_project=request.session[token]["projectID"]),
                Id_member_share=Member.objects.get(Id_member=request.session[token]["memberID"]),
                FileName=uploaded_file.name,
                File=uploaded_file
            )
            newFile.save()
            send["message"] = "Lưu file thành công"
        else:
            send["message"] = "Không thể lưu, kích thước file quá lớn"
    files = SharingFile.objects.filter(Id_project=request.session[token]["projectID"]).order_by("UploadDate")
    sendFiles = []
    for f in files:
        sendFiles.append({"name":f.FileName,"uploader":f.Id_member_share.Id_user.Username,"uploadDate":f.UploadDate.strftime("%Y/%m/%d"),"url":f.File.url,"fullUploadDate":f.UploadDate.strftime("%Y-%m-%d %H:%M:%S.%f")})
    send["files"] = sendFiles
    return render(request, "project/sharingFile.html", send)

def downloadFile(request):
    file_path = os.getcwd()+request.GET['url']
    fileName = request.GET['name']
    fileName = remove_diacritics(fileName)
    if not os.path.exists(file_path):
        return HttpResponse("Không tìm thấy file", status=404)
    else:
        with open(file_path, 'rb') as f:
            response = HttpResponse(f)
            response['Content-Type'] = 'application/octet-stream'
            response['Content-Disposition'] = f'attachment; filename="{fileName}"'.format(os.path.basename(file_path))
            return response

def watchFile(request):
    file_path = os.getcwd()+request.GET['url']
    filename = request.GET['name']

    if is_image(file_path):
        image = Image.open(file_path)
        buffer = io.BytesIO()
        image.save(buffer, format='PDF')
        buffer.seek(0)
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename={filename}'
        return response
    elif is_pdf(file_path):
        with open(file_path, 'rb') as pdf_file:
            pdf_content = pdf_file.read()
        response = HttpResponse(pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename="{}"'.format(os.path.basename(file_path))
        return response
    else:
        try:
            doc = Document(file_path)
    
            buffer = io.BytesIO()
            p = canvas.Canvas(buffer)
            
            p.setFont('Times-Roman', 12)

            # Lặp qua các đoạn văn trong tài liệu Word và vẽ chúng lên canvas
            y_coordinate = 800
            for paragraph in doc.paragraphs:
                p.drawString(50, y_coordinate, paragraph.text)
                y_coordinate -= 15
                if y_coordinate <= 40:
                    p.showPage()
                    y_coordinate = 800

            p.save()
            buffer.seek(0)

            response = HttpResponse(buffer, content_type='application/pdf')
            response['Content-Disposition'] = f'inline; filename={filename}'
            return response
        except Exception as e:
            print(e)
            return HttpResponse("Không hỗ trợ xem file có định dạng này")

def deleteFile(request):
    fileName = request.GET['name']
    uploadDate = request.GET['uploadDate']
    token = request.GET["token"]
    if isNotAllowToEdit(request.session[token]["projectID"]):
        return redirect(f"/main/homepage?token={token}")
    files = SharingFile.objects.filter(Id_project=request.session[token]["projectID"])
    for f in files:
        if f.FileName == fileName and f.UploadDate.strftime("%Y-%m-%d %H:%M:%S.%f") == uploadDate:
            f.delete()
            break
    return redirect(f"/project/sharingFile?token={token}")

def setAllowFinish(request, agree, token):
    if isNotAllowToEdit(request.session[token]["projectID"]):
        return redirect(f"/main/homepage?token={token}")
    me = Member.objects.get(Id_member=request.session[token]["memberID"])
    if agree == "T":
        me.AllowFinish = True
    else:
        me.AllowFinish = False
    me.save()
    return redirect(f"/project/homepage?token={token}")

def finishProject(request):
    send = {}
    token = request.GET["token"]
    if isNotAllowToEdit(request.session[token]["projectID"]):
        return redirect(f"/main/homepage?token={token}")
    send["token"]= token
    projectID = request.session[token]["projectID"]
    project = Project.objects.get(Id_project=projectID)
    if canFinishProject(projectID) and checkClientAgree(projectID):
        if request.method == "POST":
            form = FinishProjectForm(request.POST)
            if form.is_valid():
                project.Finished = True
                project.Result = form.cleaned_data["Result"]
                project.Evaluation = form.cleaned_data["Evaluation"]
                project.Handover = form.cleaned_data["Handover"]
                project.save()
                return redirect(f"/main/homepage?token={token}")
        else:
            form = FinishProjectForm()
        send["form"] = form
        return render(request, "project/finishProject.html", send)
    else:
        return redirect(f"/project/homepage?token={token}")

def summaryProject(request, projectID):
    send = {}
    token = request.GET["token"]
    x = request.session[token]
    x["projectID"] = projectID
    x["memberID"] = Member.objects.get(Id_project=projectID, Id_user=request.session[token]["userID"]).pk
    request.session[token] = x
    send["token"] = token
    project = Project.objects.get(Id_project=projectID)
    send["form"] = ShowFinishProjectForm(instance=project)
    send["projectID"] = projectID
    # ngân sách
    _ , sumBudget = getProgress(project)
    send["budget"] = project.Budget
    send["budgetUsed"] = sumBudget
    send["budgetNotUse"] = project.Budget - sumBudget
    # lấy dữ liệu lịch trình
    phases = Phase.objects.filter(Id_project=projectID).order_by("Order")
    missions = []
    dates = []
    i = 0
    for phase in phases:
        b, e = getMissionRealDate(phase.pk, "phase")
        dates += [b, e, phase.StartDate, phase.EndDate]
        tasks = Task.objects.filter(Id_phase=phase.Id_phase).order_by("Order")
        if len(tasks)!=0:
            budget = sum(task.Budget for task in tasks)
            progress = round(sum(task.Progress for task in tasks)/len(tasks))
        else:
            budget = 0
            progress = 0
        missions.append({
            "type":"phase",
            "Name":phase.PhaseName,
            "Order":phase.Order,
            "Budget":budget,
            "Progress":progress,
            "StartDate":phase.StartDate.strftime("%d/%m"),
            "EndDate":phase.EndDate.strftime("%d/%m"),
            "FullStartDate":phase.StartDate.strftime("%Y-%m-%d"),
            "FullEndDate":phase.EndDate.strftime("%Y-%m-%d"),
            "RealStartDate":b.strftime("%Y-%m-%d"),
            "RealEndDate":e.strftime("%Y-%m-%d"),
            "id":str(i),
            "ID":phase.Id_phase,
        })
        i += 1
        for task in tasks:
            b, e = getMissionRealDate(task.pk, "task")
            dates += [b, e, task.StartDate, task.EndDate]
            assign = Assign.objects.get(Id_task=task)
            assigner = assign.Id_member.Id_user.Username
            missions.append({
                "type":"task",
                "Name":task.TaskName,
                "Order":task.Order,
                "Budget":task.Budget,
                "Progress":task.Progress,
                "Description":task.Description,
                "StartDate":task.StartDate.strftime("%d/%m"),
                "EndDate":task.EndDate.strftime("%d/%m"),
                "FullStartDate":task.StartDate.strftime("%Y-%m-%d"),
                "FullEndDate":task.EndDate.strftime("%Y-%m-%d"),
                "RealStartDate":b.strftime("%Y-%m-%d"),
                "RealEndDate":e.strftime("%Y-%m-%d"),
                "id":str(i),
                "ID":task.Id_task,
                "Assign":assign,
                "Assigner":assigner
            })
            i += 1
    send["missions"] = missions
    # tạo danh sách ngày
    send["arrDates"], send["arrDatesLimit"], send["lenArr"] = arrayDates(min(dates), max(dates))
    # lấy dữ liệu người tham gia
    # quản lý dự án
    manager = Member.objects.get(Id_project=project.pk, Position="0")
    send["managerInfo"] = {"Name":manager.Id_user.Username,"Email":manager.Id_user.Email,"Avatar":manager.Id_user.Avatar.url,"GroupJoin":getGroupsJoin(manager),"Assign":getAssignTask(manager)}
    # khách hàng
    clients = Member.objects.filter(Id_project=project.pk, Position="2")
    clientList = []
    for c in clients:
        clientList.append({"Name":c.Id_user.Username,"Email":c.Id_user.Email,"Avatar":c.Id_user.Avatar.url,"GroupJoin":getGroupsJoin(c)})
    send["clientList"] = clientList
    # nhân viên
    member = Member.objects.filter(Id_project=project.pk, Position="1")
    memberList = []
    for m in member:
        memberList.append({"Name":m.Id_user.Username,"Email":m.Id_user.Email,"Avatar":m.Id_user.Avatar.url,"GroupJoin":getGroupsJoin(m),"Assign":getAssignTask(m)})
    send["memberList"] = memberList
    # báo cáo
    # báo cáo dự án
    projectReposts = ProjectRepost.objects.filter(Id_project=projectID).order_by("-DateRepost")
    sendReposts = []
    for pr in projectReposts:
        sendReposts.append({"id":pr.Id_repost,"date":pr.DateRepost.strftime("%Y-%m-%d, %I:%M %p")})
    send["reposts"] = sendReposts
    send["lenRepost"] = len(sendReposts)
    # file chia sẻ
    files = SharingFile.objects.filter(Id_project=projectID).order_by("UploadDate")
    sendFiles = []
    for f in files:
        sendFiles.append({"name":f.FileName,"uploader":f.Id_member_share.Id_user.Username,"uploadDate":f.UploadDate.strftime("%Y/%m/%d"),"url":f.File.url,"fullUploadDate":f.UploadDate.strftime("%Y-%m-%d %H:%M:%S.%f")})
    send["files"] = sendFiles
    return render(request, "project/summary.html", send)

def groupHomepage(request):
    token = request.GET["token"]
    return redirect(f"/group/homepage?token={token}")

def videoCall(request):
    token = request.GET["token"]
    return redirect(f"/main/videoCall?token={token}")