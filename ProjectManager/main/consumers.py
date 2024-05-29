import json, time
from django.db.models import Q
from channels.generic.websocket import AsyncWebsocketConsumer, WebsocketConsumer
from channels.db import database_sync_to_async
from asgiref.sync import async_to_sync
from asgiref.sync import sync_to_async
from .models import *
from .forms import *

def allowManager(memberID, projectID):
    try:
        member = Member.objects.get(Id_project=projectID, Id_member=memberID)
        if member.Position == "0":
            return True
        else:
            return False
    except:
        return False

def allowCaptain(groupID, partID):
    try:
        part = Participant.objects.get(Id_group=groupID, Id_participant=partID)
        if part.Position == "0":
            return True
        else:
            return False
    except:
        return False

def sumBudget(project):
    s = 0
    phases = Phase.objects.filter(Id_project=project)
    for phase in phases:
        tasks = Task.objects.filter(Id_phase=phase)
        for task in tasks:
            s += task.Budget
    return s
    
class SupportHandel(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = f"support_{self.scope['url_route']['kwargs']['support_id']}"
        self.support = await self.get_support_chat()
        await self.channel_layer.group_add(self.room_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        sm = await self.handle_message(data)
        if data['type'] == 'message':
            event = {
                "type": "send_message",
                "data":sm,
            }
            await self.channel_layer.group_send(self.room_name, event)
    
    async def send_message(self, event):
        data = event['data']
        response_data = {
            "content": data.Content,
            "time": data.SendDate.strftime("%Y-%m-%d, %I:%M %p"),
            "reply": data.Reply
        }
        await self.send(text_data=json.dumps({'data': response_data}))

    @sync_to_async
    def get_support_chat(self):
        support_id = self.scope['url_route']['kwargs']['support_id']
        return SupportChat.objects.get(Id_supportChat=support_id)

    @sync_to_async
    def handle_message(self, data):
        sm = SupportMessage.objects.create(
            Id_supportChat=self.support,
            Content=data["content"],
            Reply=data["sender"] == "a"
        )
        return sm
    
class GroupChatHandel(AsyncWebsocketConsumer):
    async def connect(self):
        self.groupID = self.scope['url_route']['kwargs']['group_id']
        self.participantID = self.scope['url_route']['kwargs']['participant_id']
        self.memberID = self.scope['url_route']['kwargs']['member_id']
        if await self.checkParticipant():
            self.group_name = f"group_{self.groupID}"
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        if await self.allowToJoin():
            if data['type'] == 'request' and data['request'] == "getAllMessage":
                await self.send(json.dumps({
                    'type':'allMessage',
                    'groupID':self.groupID,
                    'messages':await self.getAllMessage(),
                    'position':self.part.Position,
                    'participants':await self.getAllParticipant(),
                }))
            if data['type'] == 'request' and data['request'] == "delete":
                response_data = await self.deleteGroup()
                if response_data:
                    await self.send_to_group(response_data)
            if data["type"] == 'message':
                response_data = await self.handle_message(data)
                await self.send_to_group(response_data)
            if data["type"] == 'delMess':
                if await self.deleteMess(data["messID"]):
                    response_data = await self.handle_delMess(data)
                    await self.send_to_group(response_data)
                else:
                    await self.send(json.dumps({"type":"respone","content":"Xóa tin nhắn thất bại"}))
        else:
            await self.send(json.dumps({'type':'responeDel', 'content':f'Bạn không còn là thành viên của nhóm'}))
    async def send_to_group(self, response_data):
        await self.channel_layer.group_send(self.group_name, response_data)

    async def message(self, response_data):
        await self.send(json.dumps(response_data))

    async def delMess(self, response_data):
        await self.send(json.dumps(response_data))

    async def responeDel(self, response_data):
        await self.send(json.dumps(response_data))
        await self.close()

    @sync_to_async
    def handle_message(self, data):
        m = Message.objects.create(
            Id_participant=self.part,
            Content=data["content"]
        )
        response_data = {
            "type": "message",
            "ID":m.Id_message,
            "Content": m.Content,
            "SendDate": m.SendDate.strftime("%Y-%m-%d, %I:%M %p"),
            "Name": m.Id_participant.Id_member.Id_user.Username,
            "Avatar": m.Id_participant.Id_member.Id_user.Avatar.url,
            "memberID": m.Id_participant.Id_member.pk
        }
        return response_data
    
    @sync_to_async
    def handle_delMess(self, data):
        response_data = {
            "type": "delMess",
            "messID": data["messID"],
        }
        return response_data
    
    @sync_to_async
    def deleteGroup(self):
        if self.part.Position == "0":
            group = Group.objects.get(Id_group=self.groupID)
            assign = Assign.objects.filter(Id_group=self.groupID)
            for a in assign:
                a.Id_group = ""
                a.save()
            groupName = group.GroupName
            group.delete()
            response_data = {'type':'responeDel', 'content':f'Nhóm {groupName} đã bị xóa bởi trưởng nhóm'}
            return response_data
        else:
            self.send(json.dumps({'type':'respone',
                                  'content':'Từ chối xóa nhóm'}))
            return None
    
    @sync_to_async
    def getAllMessage(self):
        participants = Participant.objects.filter(Id_group=self.groupID).values("Id_participant")
        messages = Message.objects.filter(Id_participant__in=participants).order_by("-SendDate")
        sendMess = []
        for m in messages:
            sendMess.append({"ID":m.Id_message,"Content":m.Content,"SendDate":m.SendDate.strftime("%Y-%m-%d, %I:%M %p"),
                             "Name":m.Id_participant.Id_member.Id_user.Username,"Avatar":m.Id_participant.Id_member.Id_user.Avatar.url,
                             "memberID":m.Id_participant.Id_member.pk})
        return sendMess
    
    @sync_to_async
    def getAllParticipant(self):
        participants = Participant.objects.filter(Id_group=self.groupID, Join=True)
        partList = []
        for p in participants:
            u = p.Id_member.Id_user
            s = "Offline"
            if u.Online: s = "Online"
            partList.append({"Name":u.Username,
                                 "Avatar":u.Avatar.url,
                                 "Status":s})
        return partList

    
    @sync_to_async
    def checkParticipant(self):
        try:
            self.part = Participant.objects.get(Id_participant=self.participantID, Id_member=self.memberID, Id_group=self.groupID, Join=True)
            return True
        except:
            return False
        
    @database_sync_to_async
    def deleteMess(self, id):
        try:
            mess = Message.objects.get(Id_message=id)
            mess.delete()
            return True
        except:
            return False
        
    @database_sync_to_async
    def allowToJoin(self):
        try:
            part = Participant.objects.get(Id_participant=self.participantID)
            return part.Join
        except:
            return False

class OnlineChecker(WebsocketConsumer):
    def connect(self):
        self.accept()
        self.userID = self.scope['url_route']['kwargs']['user_id']
        try:
            user = User.objects.get(Id_user=self.userID)
            user.Online = True
            user.save()
        except:
            self.close()

    def disconnect(self, code=None, reason=None):
        user = User.objects.get(Id_user=self.userID)
        user.Online = False
        user.save()

class MemberHandel(WebsocketConsumer):
    def connect(self):
        self.accept()
        self.memberID = self.scope['url_route']['kwargs']['member_id']
        self.projectID = self.scope['url_route']['kwargs']['project_id']
        self.project = Project.objects.get(Id_project=self.projectID)
        if not allowManager(self.memberID, self.projectID):
            self.close()

    def disconnect(self, code=None, reason=None):
        pass

    def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        if data["type"] == "add":
            try:
                user = User.objects.get(Id_user=data["userID"])
                pos = TypePosition.TYPE2
                if user.TypeUser == "0":
                    pos = TypePosition.TYPE1
                newMember = Member.objects.create(Id_project=self.project,Id_user=user,Position=pos)
                newMember.save()
                self.send(json.dumps({"type":"respone", "content":"Thêm thành viên thành công"}))
            except Exception as e:
                print(e)
                self.send(json.dumps({"type":"respone", "content":"Thêm thành viên thất bại"}))
        if data["type"] == "remove":
            members = Member.objects.filter(Id_member__in=data["listMemberID"])
            try:
                members.delete()
                self.send(json.dumps({"type":"respone", "content":"Xóa thành viên thành công"}))
            except Exception as e:
                print(e)
                self.send(json.dumps({"type":"respone", "content":"Xóa thành viên thất bại"}))

class ParticipantHandel(WebsocketConsumer):
    def connect(self):
        self.accept()
        self.groupID = self.scope['url_route']['kwargs']['group_id']
        self.partID = self.scope['url_route']['kwargs']['part_id']
        self.group = Group.objects.get(Id_group=self.groupID)
        if not allowCaptain(self.groupID, self.partID):
            self.close()
    
    def disconnect(self, code=None, reason=None):
        pass

    def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        if not allowCaptain(self.groupID, self.partID):
            self.send(json.dumps({'type':'respone',
                                    'content':'Bạn không có quyền chỉnh sửa nhóm'}))
        if data["type"] == "add" and data["groupID"] == self.groupID:
            numberPart = len(Participant.objects.filter(Id_group=self.groupID, Join=True))
            if numberPart + 1 <= self.group.MaxNumber:
                try:
                    oldPart = Participant.objects.get(Id_member=Member.objects.get(Id_member=data["memberID"]),
                                                    Id_group=self.group)
                    oldPart.Join = True
                    oldPart.save()
                    self.send(json.dumps({'type':'respone',
                                    'content':'Đã thêm thành viên cũ vào lại nhóm'}))
                except:
                    newPart = Participant.objects.create(Id_member=Member.objects.get(Id_member=data["memberID"]),
                                                        Id_group=self.group,
                                                        Position=TypeGroupPosition.TYPE1)
                    newPart.save()
                    self.send(json.dumps({'type':'respone',
                                        'content':'Đã thêm thành viên nhóm mới'}))
                return
            else:
                self.send(json.dumps({'type':'respone',
                                    'content':f'Không thể thêm. Nhóm đã đủ: {self.group.MaxNumber} thành viên'}))
                return
        if data["type"] == "remove" and data["groupID"] == self.groupID:
            try:
                removePart = Participant.objects.get(Id_participant=data["partID"])
                removePart.Join = False
                removePart.save()
                self.send(json.dumps({'type':'respone',
                                    'content':'Đã cách chức thành viên ra khỏi nhóm',
                                    'success':True}))
            except:
                self.send(json.dumps({'type':'respone',
                                    'content':'Có lỗi xảy ra. Cách chức thất bại.'}))
            return
        if data["type"] == "update" and data["groupID"] == self.groupID:
            try:
                updatePart = Participant.objects.get(Id_participant=data["partID"])
                updatePart.Position = data["newPos"]
                updatePart.save()
            except:
                self.send(json.dumps({'type':'respone',
                                    'content':'Có lỗi xảy ra. Đặt chức vụ thất bại.'}))
            return

class GetRepostHandel(WebsocketConsumer):
    def connect(self):
        self.projectID = self.scope['url_route']['kwargs']['project_id']
        self.accept()
    
    def close(self, code=None, reason=None):
        pass

    def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        assign = Assign.objects.get(Id_task=data["task"])
        repost = Repost.objects.filter(Id_assign=assign.pk).order_by("-DateRepost")
        repostList = []
        for r in repost:
            repostList.append({"date":r.DateRepost.strftime("%Y-%m-%d, %I:%M %p"), "id":r.pk})
        self.send(json.dumps({"type":"repost", "list":repostList}))
        check = Check.objects.filter(Id_assign=assign.pk).order_by("-DateCheck")
        checkList = []
        for c in check:
            checkList.append({"date":c.DateCheck.strftime("%Y-%m-%d, %I:%M %p"), "id":c.pk})
        self.send(json.dumps({"type":"check", "list":checkList}))

class ScheduleHandel(WebsocketConsumer):
    def connect(self):
        self.accept()
    
    def close(self, code=None, reason=None):
        pass

    def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        # tạo assign
        if data["option"] == "addAssign":
            try:
                assign = Assign.objects.get(Id_task=data["taskID"])
                assign.Id_member=Member.objects.get(Id_member=data["memberID"])
                assign.Id_group=Group.objects.get(Id_group=data["groupID"]).pk
                assign.save()
            except Assign.DoesNotExist:
                newAssign = Assign.objects.create(Id_task=Task.objects.get(Id_task=data["taskID"]), 
                                                  Id_member=Member.objects.get(Id_member=data["memberID"]), 
                                                  Id_group=data["groupID"])
                newAssign.save()
            self.send(json.dumps({"type":"respone", "content":"Đã lưu phân công", "reload":True}))
        # thiết lập data cho assign form
        if data["option"] == "?assign":
            try:
                # đã được phân công
                assign = Assign.objects.get(Id_task=data["taskID"])
                if assign.Id_group == "":
                    members = Member.objects.filter(Id_project=data["projectID"]).exclude(Position="2")
                    sendMem = []
                    for m in members:
                        sendMem.append({"id":m.pk, "name":m.Id_user.Username})
                    self.send(json.dumps({"type":"setupAssignSave","members":sendMem,"selectedMem":assign.Id_member.pk,"selectedGroup":assign.Id_group}))
                else:
                    p = Participant.objects.filter(Id_group=assign.Id_group, Join=True).values("Id_member")
                    members = Member.objects.filter(Id_member__in=p).exclude(Position="2")
                    sendMem = []
                    for m in members:
                        sendMem.append({"id":m.pk, "name":m.Id_user.Username})
                    self.send(json.dumps({"type":"setupAssignSave","members":sendMem,"selectedMem":assign.Id_member.pk,"selectedGroup":assign.Id_group}))
            except Assign.DoesNotExist:
                # chưa được phân công
                members = Member.objects.filter(Id_project=data["projectID"]).exclude(Position="2")
                sendMem = []
                for m in members:
                    sendMem.append({"id":m.pk, "name":m.Id_user.Username})
                self.send(json.dumps({"type":"setupAssign","members":sendMem}))
        # trả lại danh sách member mới
        if data['option'] == 'getOptionAssign':
            if data['groupID'] != "":
                p = Participant.objects.filter(Id_group=data["groupID"], Join=True).values("Id_member")
                members = Member.objects.filter(Id_member__in=p).exclude(Position="2")
                sendMem = []
                for m in members:
                    sendMem.append({"id":m.pk, "name":m.Id_user.Username})
                self.send(json.dumps({"type":"responeAssign","members":sendMem}))
            else:
                members = Member.objects.filter(Id_project=data["projectID"]).exclude(Position="2")
                sendMem = []
                for m in members:
                    sendMem.append({"id":m.pk, "name":m.Id_user.Username})
                self.send(json.dumps({"type":"responeAssign","members":sendMem}))
        # thêm giai đoạn
        if data['option'] == "add" and data['obj_Type'] == "phase":
            if allowManager(data["memberID"], data["projectID"]):
                form = MakePhaseForm(data=data["formData"])
                if form.is_valid() and form.is_dateCorrect():
                    try:
                        otherPhase = Phase.objects.filter(Id_project=data["projectID"]).order_by("Order")
                        x = True
                        for phase in otherPhase:
                            if phase.PhaseName == data["formData"]["PhaseName"]:
                                x = False
                                break
                        if x:
                            for phase in otherPhase:
                                if phase.Order >= int(data["order"])+1:
                                    phase.Order = phase.Order + 1
                                    phase.save()
                            newPhase = Phase.objects.create(
                                Id_project=Project.objects.get(Id_project=data["projectID"]),
                                PhaseName = data["formData"]["PhaseName"],
                                Order = int(data["order"])+1,
                                StartDate = data["formData"]["StartDate"],
                                EndDate = data["formData"]["EndDate"],
                            )
                            newPhase.save()
                        else:
                            self.send(json.dumps({"type":"respone", "content":"Tên giai đoạn bị trùng", "reload":False}))
                    except Exception as e:
                        print(e)
                    self.send(json.dumps({"type":"reload"}))
                else:
                    self.send(json.dumps({"type":"respone", "content":"Dữ liệu nhập không hợp lệ", "reload":False}))
            else:
                self.send(json.dumps({"type":"respone", "content":"Từ chối chỉnh sửa", "reload":False}))
        # sửa giai đoạn
        if data['option'] == "edit" and data['obj_Type'] == "phase":
            if allowManager(data["memberID"], data["projectID"]):
                form = MakePhaseForm(data=data["formData"])
                if form.is_valid() and form.is_dateCorrect():
                    try:
                        editPhase = Phase.objects.get(Id_phase=data["id"])
                        editPhase.PhaseName = data["formData"]["PhaseName"]
                        editPhase.StartDate = form.cleaned_data["StartDate"]
                        editPhase.EndDate = form.cleaned_data["EndDate"]
                        editPhase.save()
                        self.send(json.dumps({"type":"reload"}))
                    except Exception as e:
                        print(e)
                else:
                    self.send(json.dumps({"type":"respone", "content":"Dữ liệu nhập không hợp lệ", "reload":False}))
            else:
                self.send(json.dumps({"type":"respone", "content":"Từ chối chỉnh sửa", "reload":False}))
        # xóa giai đoạn
        if data['option'] == "delete" and data['obj_Type'] == "phase":
            if allowManager(data["memberID"], data["projectID"]):
                try:
                    deletePhase = Phase.objects.get(Id_phase=data["phaseID"])
                    deletePhase.delete()
                    otherPhase = Phase.objects.filter(Id_project=data["projectID"]).order_by("Order")
                    for phase in otherPhase:
                        if phase.Order > int(data["order"]):
                            phase.Order = phase.Order - 1
                            phase.save()
                except Exception as e:
                    print(e)
                self.send(json.dumps({"type":"reload"}))
            else:
                self.send(json.dumps({"type":"respone", "content":"Từ chối chỉnh sửa", "reload":False}))
        # thêm nhiệm vụ
        if data['option'] == "add" and data['obj_Type'] == "task":
            if allowManager(data["memberID"], data["projectID"]):
                form = MakeTaskForm(data=data["formData"])
                if form.is_valid() and form.is_dateCorrect():
                    project = Project.objects.get(Id_project=data["projectID"])
                    if data["phaseID"]=="None":
                        phase = Task.objects.get(Id_task=data["taskID"]).Id_phase
                    else:
                        phase = Phase.objects.get(Id_phase=data["phaseID"])
                    if form.is_inPhase(phase.StartDate, phase.EndDate):
                        if sumBudget(project) + int(data["formData"]["Budget"]) <= project.Budget:
                            try:
                                otherTask = Task.objects.filter(Id_phase=phase.Id_phase).order_by("Order")
                                for task in otherTask:
                                    if task.Order >= int(data["order"])+1:
                                        task.Order = task.Order + 1
                                        task.save()
                                newTask = Task.objects.create(
                                    Id_phase = phase,
                                    TaskName = data["formData"]["TaskName"],
                                    Order = int(data["order"])+1,
                                    Description = data["formData"]["Description"],
                                    Budget = int(data["formData"]["Budget"]),
                                    StartDate = data["formData"]["StartDate"],
                                    EndDate = data["formData"]["EndDate"],
                                )
                                newTask.save()
                                self.send(json.dumps({"type":"reload"}))
                            except Exception as e:
                                print(e)
                        else:
                            self.send(json.dumps({"type":"respone", "content":"Vượt ngân sách dự án", "reload":False}))
                    else:
                        self.send(json.dumps({"type":"respone", "content":"Ngày thực hiện phải ở trong phạm vi giai đoạn", "reload":False}))
                else:
                    self.send(json.dumps({"type":"respone", "content":"Dữ liệu nhập không hợp lệ", "reload":False}))
            else:
                self.send(json.dumps({"type":"respone", "content":"Từ chối chỉnh sửa", "reload":False}))
        # sửa nhiệm vụ
        if data['option'] == "edit" and data['obj_Type'] == "task":
            if allowManager(data["memberID"], data["projectID"]):
                form = MakeTaskForm(data=data["formData"])
                if form.is_valid() and form.is_dateCorrect():
                    project = Project.objects.get(Id_project=data["projectID"])
                    phase = Task.objects.get(Id_task=data["taskID"]).Id_phase
                    if form.is_inPhase(phase.StartDate, phase.EndDate):
                        if sumBudget(project) + int(data["formData"]["Budget"]) <= project.Budget:
                            try:
                                editTask = Task.objects.get(Id_task=data["taskID"])
                                editTask.TaskName = data["formData"]["TaskName"]
                                editTask.Description = data["formData"]["Description"]
                                editTask.Budget = int(data["formData"]["Budget"])
                                editTask.StartDate = form.cleaned_data["StartDate"]
                                editTask.EndDate = form.cleaned_data["EndDate"]
                                editTask.save()
                                self.send(json.dumps({"type":"reload"}))
                            except Exception as e:
                                print(e)
                        else:
                            self.send(json.dumps({"type":"respone", "content":"Vượt ngân sách dự án", "reload":False}))
                    else:
                        self.send(json.dumps({"type":"respone", "content":"Ngày thực hiện phải ở trong phạm vi giai đoạn", "reload":False}))
                else:
                    self.send(json.dumps({"type":"respone", "content":"Dữ liệu nhập không hợp lệ", "reload":False}))
            else:
                self.send(json.dumps({"type":"respone", "content":"Từ chối chỉnh sửa", "reload":False}))
        # xóa nhiệm vụ
        if data['option'] == "delete" and data['obj_Type'] == "task":
            if allowManager(data["memberID"], data["projectID"]):
                phase = Task.objects.get(Id_task=data["taskID"]).Id_phase
                try:
                    deleteTask = Task.objects.get(Id_task=data["taskID"])
                    deleteTask.delete()
                    otherTask = Task.objects.filter(Id_phase=phase).order_by("Order")
                    for task in otherTask:
                        if task.Order > int(data["order"]):
                            task.Order = task.Order - 1
                            task.save()
                except Exception as e:
                    print(e)
                self.send(json.dumps({"type":"reload"}))
            else:
                self.send(json.dumps({"type":"respone", "content":"Từ chối chỉnh sửa", "reload":False}))
    
class VideoCallHandel(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            self.memberID = self.scope['url_route']['kwargs']['memberID']
            self.type = self.scope['url_route']['kwargs']['type'] # 'project' or 'group'
            self.id = self.scope['url_route']['kwargs']['id'] # id project or id group
            self.masterID = None
            self.name = None
            self.avatar = None
            await self.getName()
            await self.getAvatar()
            if self.type == "project":
                await self.getMember()
                if self.member.Position == "0":
                    # bắt đầu cuộc gọi all
                    await self.createVideoCall()
                    self.masterID = self.memberID
                    self.video_call = f"video_call_{self.videoCall.pk}"
                    await self.channel_layer.group_add(self.video_call, self.channel_name)
                    await self.accept()
                    await self.send(json.dumps({
                        "type":"order",
                        "order":"ready"
                    }))
                else:
                    # thử xem có cuộc gọi project để tham gia ko
                    await self.accept()
                    if self.isProjectMember():
                        try:
                            await self.getVideoCall()
                            await self.getMasterID()
                            self.video_call = f"video_call_{self.videoCall.pk}"
                            await self.channel_layer.group_add(self.video_call, self.channel_name)

                            userID = await self.getConnections()
                            if len(userID) == 0:
                                userID.append(self.masterID)
                            await self.send(json.dumps({
                                "type":"getUserID",
                                "userIDs":userID
                            }))
                        except Exception as e:
                            # không có cuộc gọi
                            print(e)
                            await self.send(json.dumps({
                                "type":"noCall"
                            }))
                            self.close()
                    else:
                        self.close()
        except:
            pass

    async def disconnect(self, code):
        if self.type == "project":
            try:
                if self.memberID == self.masterID:
                    await self.deleteVideoCall()
                    await self.send_to_group({"type":"order", "order":"allOut"})
                else:
                    await self.deleteVideoConnect()
                    await self.send_to_group({"type":"order", "order":"memberOut", "memberID":self.memberID})
                await self.channel_layer.group_discard(self.video_call, self.channel_name)
            except Exception as e:
                print(e)

    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        if data["type"] == "offer":
            await self.resetVideoConnect(data["caller"], data["callee"])
            await self.createVideoConnect(data["caller"], data["callee"])
            # gửi offer tới người gọi tới
            response_data = await self.makeOfferMess(data["caller"], data["callee"], data["offer"])
            await self.send_to_group(response_data)
            return
        if data["type"] == "answer":
            # gửi answer cho người gọi đi
            response_data = await self.makeAnswerMess(data["caller"], data["callee"], data["answer"], data["camera"])
            await self.send_to_group(response_data)
            return
        if data["type"] == "ice":
            if data["sender"] == "caller":
                response_data = await self.makeIceMess(data["caller"], data["callee"], data["icecandidate"])
            else:
                response_data = await self.makeIceMess(data["callee"], data["caller"], data["icecandidate"])
            await self.send_to_group(response_data)
            return
        if data["type"] == "order":
            if data["order"] == "stopWatch":
                response_data = self.makeStopWatchMess(data["myID"])
                await self.send_to_group(response_data)
                return
            if data["order"] == "reWatch":
                response_data = self.makeReWatchMess(data["myID"])
                await self.send_to_group(response_data)
                return


    async def send_to_group(self, data):
        await self.channel_layer.group_send(self.video_call, data)

    async def order(self, data):
        await self.send(json.dumps(data))

    async def offer(self, response_data):
        if str(response_data["callee"]) == self.memberID:
            await self.send(json.dumps(response_data))
    
    async def answer(self, response_data):
        if str(response_data["caller"]) == self.memberID:
            await self.send(json.dumps(response_data))

    async def ice(self, response_data):
        if str(response_data["receiver"]) == self.memberID:
            await self.send(json.dumps(response_data))
    
    async def stopWatch(self, response_data):
        if str(response_data["memberID"]) != self.memberID:
            await self.send(json.dumps(response_data))
    
    async def reWatch(self, response_data):
        if str(response_data["memberID"]) != self.memberID:
            await self.send(json.dumps(response_data))

    @sync_to_async
    def makeOfferMess(self, callerID, calleeID, offer):
        response_data = {
            "type":"offer",
            "callerName":self.name,
            "callerAvatar":self.avatar,
            "caller":callerID,
            "callee":calleeID,
            "offer":offer,
        }
        return response_data
    
    @sync_to_async
    def makeAnswerMess(self, callerID, calleeID, answer, camera):
        response_data = {
            "type":"answer",
            "calleeName":self.name,
            "calleeAvatar":self.avatar,
            "caller":callerID,
            "callee":calleeID,
            "answer":answer,
            "camera":camera
        }
        return response_data
    
    @sync_to_async
    def makeIceMess(self, sender, receiver, ice):
        response_data = {
            "type":"ice",
            "sender":sender,
            "receiver":receiver,
            "ice":ice
        }
        return response_data
    
    def makeStopWatchMess(self, memberID):
        response_data = {
            "type":"stopWatch",
            "memberID":memberID,
        }
        return response_data
    
    def makeReWatchMess(self, memberID):
        response_data = {
            "type":"reWatch",
            "memberID":memberID,
        }
        return response_data

    @database_sync_to_async
    def getMember(self):
        self.member = Member.objects.get(Id_member=self.memberID)

    @database_sync_to_async
    def getName(self):
        self.name = Member.objects.get(Id_member=self.memberID).Id_user.Username

    @database_sync_to_async
    def getAvatar(self):
        self.avatar = Member.objects.get(Id_member=self.memberID).Id_user.Avatar.url

    @database_sync_to_async
    def createVideoCall(self):
        oldVideoCall = VideoCall.objects.filter(Limited=f"{self.type};{self.id}")
        for v in oldVideoCall:
            v.delete()
        self.videoCall = VideoCall.objects.create(Limited=f"{self.type};{self.id}")

    @database_sync_to_async
    def isProjectMember(self):
        try:
            m = Member.objects.get(Id_member=self.memberID, Id_project=self.id)
            return True
        except:
            return False

    @database_sync_to_async
    def resetVideoConnect(self, callerID, calleeID):
        try:
            vc = VideoConnect.objects.get(Id_call=self.videoCall, Id_caller=callerID, Id_callee=calleeID)
            vc.delete()
        except:
            pass
        try:
            vc = VideoConnect.objects.get(Id_call=self.videoCall, Id_caller=calleeID, Id_callee=callerID)
            vc.delete()
        except:
            pass

    @database_sync_to_async
    def createVideoConnect(self, callerID, calleeID):
        newVC = VideoConnect.objects.create(Id_call=self.videoCall, 
                                            Id_caller=Member.objects.get(Id_member=callerID),
                                            Id_callee=Member.objects.get(Id_member=calleeID))
        newVC.save()

    @database_sync_to_async
    def deleteVideoCall(self):
        self.videoCall.delete()

    @database_sync_to_async
    def deleteVideoConnect(self):
        videoConnects = VideoConnect.objects.filter(Q(Id_caller=self.memberID) | Q(Id_callee=self.memberID))
        videoConnects.delete()

    @database_sync_to_async
    def getVideoCall(self):
        self.videoCall = VideoCall.objects.get(Limited=f"{self.type};{self.id}")

    @database_sync_to_async
    def getMasterID(self):
        self.masterID = Member.objects.get(Id_project=self.id, Position="0").pk

    @database_sync_to_async
    def getConnections(self):
        connects = VideoConnect.objects.filter(Id_call=self.videoCall.pk)
        connList = []
        for conn in connects:
            if conn.Id_caller.pk not in connList:
                connList.append(conn.Id_caller.pk)
            if conn.Id_callee.pk not in connList:
                connList.append(conn.Id_callee.pk)
        return connList