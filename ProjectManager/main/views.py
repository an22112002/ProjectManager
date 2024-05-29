from django.shortcuts import render, redirect
from .forms import *
from .models import *
from .supposter import *
import os, datetime

# Create your views here.

def test(request):
    return render(request, "test.html")

def login(request):
    send = {}
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            # kiểm tra 
            users = User.objects.filter(Username=name)
            if len(users) == 0:
                # tài khoản không tồn tại
                send["mess"] = "Tài khoản không tồn tại"
            else:
                for user in users:
                    if encodePassword(user.Spice, password) == user.EncodePass:
                        if user.Lock == True:
                            send["mess"] = "Tài khoản bị khóa"
                            break
                        elif user.Online == True:
                            send["mess"] = "Tài khoản đang được sử dụng"
                            break
                        else:
                            # mật khẩu đúng, không bị khóa, lưu đăng nhập người dùng và chyển đến trang chủ
                            while True:
                                token = randomString(10)
                                if token not in request.session:
                                    request.session[token] = {"userID":user.Id_user}
                                    break
                            return redirect(f"/main/homepage?token={token}")
                    else:
                        # mật khẩu sai
                        send["mess"] = "Sai mật khẩu"
        send["form"] = form
    else:
        send["form"] = LoginForm()
    return render(request, "main/login.html", send)

def signup(request):
    send = {}
    if request.method == "POST":
        form = SignupForm(request.POST)
        allow = True
        if form.is_valid():
            name = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            typeUser = form.cleaned_data["typeUser"]
            users = User.objects.filter(Username=name)
            if len(users) != 0:
                for user in users:
                    if user.EncodePass == encodePassword(user.Spice, password):
                        allow = False
                        break
            if allow:
                spice = randomString(10)
                encodePass = encodePassword(spice, password)
                newUser = User.objects.create(Username=name, Spice=spice, EncodePass=encodePass, TypeUser=typeUser)
                newUser.save()
                return redirect("/main/login")
            else:
                send["mess"] = "Tài khoản đã tồn tại"
        send["form"] = form
    else:
        send["form"] = SignupForm()
    return render(request, "main/signup.html", send)

def logout(request):
    # xóa session
    token = request.GET["token"]
    user = User.objects.get(Id_user=request.session[token]["userID"])
    user.Online = False
    user.save()
    del request.session[token]
    return redirect("login page")

def support(request, position, supportID):
    send = {}
    send['position'] = position
    send['supportID'] = supportID
    messages = SupportMessage.objects.filter(Id_supportChat=supportID).order_by('-SendDate')
    sendMess = []
    for m in messages:
        sendMess.append({"Reply":m.Reply, "Content":m.Content, "SendDate":m.SendDate.strftime("%Y-%m-%d, %I:%M %p")})
    send["messages"] = sendMess
    return render(request, "main/support.html", send)

def homepage(request):
    send = {}
    token = request.GET["token"]
    send["token"] = token
    send["userID"] = request.session[token]["userID"]
    userId = request.session[token]["userID"]
    today = datetime.datetime.now().date()
    support = SupportChat.objects.get(Id_user=userId)
    send["support"] = support.pk
    membersProjects = Member.objects.filter(Id_user=userId)
    projectJoin = []
    unfinishTask = []
    for m in membersProjects:
        projectJoin.append({'id_project':m.Id_project,'id_member':m.Id_member,'NameProject':m.Id_project.NameProject,'Status':m.Id_project.Finished})
        assign = Assign.objects.filter(Id_member=m)
        for a in assign:
            if a.Id_task.Progress < 100:
                unfinishTask.append({"NameTask":a.Id_task.TaskName,"NameProject":a.Id_task.Id_phase.Id_project.NameProject,"Status":getStatus(today, a.Id_task.StartDate, a.Id_task.EndDate, a.Id_task.Progress)})
    send["membersProjects"] = projectJoin
    unfinishTask = reorderTask(unfinishTask)
    if len(unfinishTask) != 0:
        send["unfinishTasks"] = unfinishTask
    send["username"] = User.objects.get(Id_user=userId).Username
    send["position"] = User.objects.get(Id_user=userId).TypeUser
    return render(request, "main/homepage.html", send)

def createProject(request):
    send = {}
    token = request.GET["token"]
    send["userID"] = request.session[token]["userID"]
    send["token"] = token
    userId = request.session[token]["userID"]
    if request.method == "POST":
        form = CreateProjectForm(request.POST)
        if form.is_valid():
            newProject = form.save()
            # tạo trưởng dự án
            newMember = Member.objects.create(Id_project=newProject, Id_user=User.objects.get(Id_user=userId), Position=TypePosition.TYPE0)
            newMember.save()
            return redirect(f"/main/homepage?token={token}")
        send["form"] = form
    else:
        send["form"] = CreateProjectForm()
    return render(request, "main/createProject.html", send)

def changePass(request):
    send = {}
    token = request.GET["token"]
    send["token"] = token
    send["userID"] = request.session[token]["userID"]
    userId = request.session[token]["userID"]
    if request.method == "POST":
        form = ChangePassForm(request.POST)
        if form.is_valid():
            old_pass = form.cleaned_data["last_password"]
            new_pass = form.cleaned_data["new_password"]
            re_pass = form.cleaned_data["re_password"]
            user = User.objects.get(Id_user=userId)
            if re_pass != new_pass:
                send["mess"] = "Mật khẩu xác nhận không đúng"
            elif encodePassword(user.Spice, old_pass) != user.EncodePass:
                send["mess"] = "Mật khẩu hiện tại nhập sai"
            else:
                # chấp nhận mật khẩu mới
                newSpice = randomString(10)
                newEncodePass = encodePassword(newSpice, new_pass)
                user.Spice = newSpice
                user.EncodePass = newEncodePass
                user.save()
                return redirect(f"/main/homepage?token={token}")
        send["form"] = form
    else:
        send["form"] = ChangePassForm()
    return render(request, "main/changePass.html", send)

def editAccount(request):
    send = {}
    token = request.GET["token"]
    send["token"] = token
    userId = request.session[token]["userID"]
    user = User.objects.get(Id_user=userId)
    send["avatar"] = user.Avatar.url
    if request.method == "POST":
        form = EditAccountForm(request.POST, request.FILES)
        if form.is_valid():
            username = form.cleaned_data["Username"]
            email = form.cleaned_data["Email"]
            avatar = form.cleaned_data["Avatar"]
            user.Username = username
            user.Email = email
            if avatar:
                file = avatar
                if is_image(file):
                    old_avatar = user.Avatar
                    if old_avatar.url != "/avatars/default_avatar.png":
                        try:
                            os.remove(os.getcwd() + old_avatar.url)
                        except:
                            pass
                    user.Avatar = file
            user.save()
            return redirect(f"/main/homepage?token={token}")
        send["form"] = form
    else:
        send["form"] = EditAccountForm(instance=user)
    return render(request, "main/editAccount.html", send)

def projectHomepage(request, projectID, memberID):
    token = request.GET["token"]
    x = request.session[token]
    x["projectID"] = projectID
    x["memberID"] = memberID
    request.session[token] = x
    return redirect(f"/project/homepage?token={token}")

def videoCall(request):
    send = {}
    token = request.GET["token"]
    send["userID"] = request.session[token]["userID"]
    send["token"] = token
    send["type"] = "project"
    send["id"] = request.session[token]["projectID"]
    send["memberID"] = request.session[token]["memberID"]
    return render(request, "main/videoCall.html", send)