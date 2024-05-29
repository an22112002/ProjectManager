from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, MinLengthValidator
from PIL import Image
from django.db.models.signals import pre_delete
from django.dispatch import receiver
import os

class TypeUsers(models.TextChoices):
    TYPE0 = "0", "Thành viên phát triển dự án"
    TYPE1 = "1", "Khách hàng"

class TypePosition(models.TextChoices):
    TYPE0 = "0", "Quản lý dự án"
    TYPE1 = "1", "Nhân viên"
    TYPE2 = "2", "Khách hàng"

class TypeGroupPosition(models.TextChoices):
    TYPE0 = "0", "Trưởng nhóm"
    TYPE1 = "1", "Thành viên"

class TypeMaxMemberNumber(models.IntegerChoices):
    TYPE0 = 5, "5 thành viên"
    TYPE1 = 10, "10 thành viên"
    TYPE2 = 20, "20 thành viên"
    TYPE3 = 50, "50 thành viên"

class User(models.Model):
    Id_user = models.AutoField(primary_key=True)
    Username = models.TextField(validators=[MinLengthValidator(8)], null=False)
    Spice = models.CharField(max_length=10)
    EncodePass = models.CharField(max_length=64)
    Email = models.EmailField(null=True, default=None)
    Avatar = models.ImageField(upload_to="avatars/", default="avatars/default_avatar.png")
    TypeUser = models.CharField(max_length=1, choices=TypeUsers.choices)
    Lock = models.BooleanField(default=False)
    Online = models.BooleanField(default=False)

    def __str__(self):
        return self.Username
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        img = Image.open(self.Avatar.path)
        # Thay đổi kích thước hình ảnh
        if img.height > 200 or img.width > 200:
            output_size = (200, 200)
            img.thumbnail(output_size)
            img.save(self.Avatar.path, quality=85)

    def delete(self, *args, **kwargs):
        if self.Avatar.url != "avatars/default_avatar.png":
            os.remove(os.getcwd() + self.Avatar.url)
        super().delete(*args, **kwargs)

class Project(models.Model):
    Id_project = models.AutoField(primary_key=True)
    NameProject = models.TextField()
    Description = models.TextField()
    Budget = models.IntegerField(validators=[MinValueValidator(0)])
    Finished = models.BooleanField(default=False)
    Result = models.TextField(default="")
    Evaluation = models.TextField(default="")
    Handover = models.TextField(default="")

    def __str__(self):
        return str(self.Id_project)

class Member(models.Model):
    Id_member = models.AutoField(primary_key=True)
    Id_project = models.ForeignKey(Project, on_delete=models.CASCADE)
    Id_user = models.ForeignKey(User, on_delete=models.CASCADE)
    Position = models.CharField(max_length=1, choices=TypePosition.choices)
    AllowFinish = models.BooleanField(default=False)

    def __str__(self):
        return str(self.Id_user)

class Phase(models.Model):
    Id_phase = models.AutoField(primary_key=True)
    Id_project = models.ForeignKey(Project, on_delete=models.CASCADE)
    PhaseName = models.TextField()
    Order = models.IntegerField()
    StartDate = models.DateField()
    EndDate = models.DateField()

class Task(models.Model):
    Id_task = models.AutoField(primary_key=True)
    Id_phase = models.ForeignKey(Phase, on_delete=models.CASCADE)
    TaskName = models.TextField()
    Order = models.IntegerField()
    Description = models.TextField()
    Budget = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    StartDate = models.DateField()
    EndDate = models.DateField()
    Progress = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])

class Assign(models.Model):
    Id_assign = models.AutoField(primary_key=True)
    Id_task = models.ForeignKey(Task, on_delete=models.CASCADE)
    Id_member = models.ForeignKey(Member, on_delete=models.CASCADE)
    Id_group = models.TextField(null=True, default=None)

class Repost(models.Model):
    Id_repost = models.AutoField(primary_key=True)
    Id_assign = models.ForeignKey(Assign, on_delete=models.CASCADE)
    Id_writer = models.ForeignKey(Member, on_delete=models.CASCADE)
    Description = models.TextField()
    Result = models.TextField()
    RealStartDate = models.DateField()
    DateRepost = models.DateTimeField(auto_now=True)

class Check(models.Model):
    Id_check = models.AutoField(primary_key=True)
    Id_writer = models.ForeignKey(Member, on_delete=models.CASCADE)
    Id_assign = models.ForeignKey(Assign, on_delete=models.CASCADE)
    Result = models.TextField()
    Progress = models.IntegerField(default=0)
    DateCheck = models.DateTimeField(auto_now=True)

class ProjectRepost(models.Model):
    Id_repost = models.AutoField(primary_key=True)
    Id_project = models.ForeignKey(Project, default=None, on_delete=models.CASCADE)
    Progress = models.TextField()
    Risk = models.TextField(null=True)
    Propose = models.TextField(null=True)
    DateRepost = models.DateTimeField(auto_now=True)

class Group(models.Model):
    Id_group = models.AutoField(primary_key=True)
    GroupName = models.TextField()
    MaxNumber = models.IntegerField(default=TypeMaxMemberNumber.TYPE0, choices=TypeMaxMemberNumber)

    def __str__(self):
        return self.GroupName

class Participant(models.Model):
    Id_participant = models.AutoField(primary_key=True)
    Id_member = models.ForeignKey(Member, on_delete=models.CASCADE)
    Id_group = models.ForeignKey(Group, on_delete=models.CASCADE)
    Position = models.CharField(max_length=1, choices=TypeGroupPosition.choices)
    Join = models.BooleanField(default=True)

class Message(models.Model):
    Id_message = models.AutoField(primary_key=True)
    Id_participant = models.ForeignKey(Participant, on_delete=models.CASCADE)
    Content = models.TextField()
    SendDate = models.DateTimeField(auto_now=True)

class SharingFile(models.Model):
    Id_project = models.ForeignKey(Project, on_delete=models.CASCADE)
    Id_member_share = models.ForeignKey(Member, on_delete=models.CASCADE)
    FileName = models.TextField()
    UploadDate = models.DateTimeField(auto_now=True)
    File = models.FileField(upload_to="sharingFiles/")

class VideoCall(models.Model):
    Id_call = models.AutoField(primary_key=True)
    Limited = models.TextField()

class VideoConnect(models.Model):
    Id_call = models.ForeignKey(VideoCall, on_delete=models.CASCADE)
    Id_caller = models.ForeignKey(Member, related_name='caller_connections', on_delete=models.CASCADE)
    Id_callee = models.ForeignKey(Member, related_name='callee_connections', on_delete=models.CASCADE)

class SupportChat(models.Model):
    Id_supportChat = models.AutoField(primary_key=True)
    Id_user = models.ForeignKey(User, on_delete=models.CASCADE)

class SupportMessage(models.Model):
    Id_supportChat = models.ForeignKey(SupportChat, on_delete=models.CASCADE)
    Content = models.TextField()
    Reply = models.BooleanField(default=True)
    SendDate = models.DateTimeField(auto_now=True)

@receiver(pre_delete, sender=SharingFile)
def delete_file(sender, instance, **kwargs):
    if instance.File:
        if os.path.isfile(instance.File.path):
            os.remove(instance.File.path)