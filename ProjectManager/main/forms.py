from typing import Any, Mapping
from django import forms
from django.contrib.admin.widgets import AdminDateWidget
from django.core.validators import RegexValidator
from django.forms.utils import ErrorList
from .models import Project, User, Repost, ProjectRepost, Group, Phase, Task, TypeUsers, Check
import datetime

class LoginForm(forms.Form):
    username = forms.CharField(max_length=None, label="Tài khoản(*)")
    password = forms.CharField(max_length=None, label="Mật khẩu(*)", widget=forms.PasswordInput)

class SignupForm(forms.Form):
    uppercase_validator = RegexValidator(
        regex=r'[A-Z]',
        message="Phải chứa ít nhất một ký tự in hoa.",
        code="no_uppercase"
    )
    number_validator = RegexValidator(
        regex=r'[0-9]',
        message="Phải chứa ít nhất một chữ số.",
        code="no_number"
    )
    special_character_validator = RegexValidator(
        regex=r'[!@#$%^&*(),.?":{}|<>]',
        message="Phải chứa ít nhất một ký tự đặc biệt.",
        code="no_special_character"
    )
    username = forms.CharField(max_length=None, label="Tài khoản(*)")
    password = forms.CharField(max_length=None, label="Mật khẩu(*)", widget=forms.PasswordInput, validators=[uppercase_validator, number_validator, special_character_validator])
    typeUser = forms.ChoiceField(choices=TypeUsers.choices, label="Loại tài khoản")
    
class CreateProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ["NameProject", "Description", "Budget"]
        labels = {"NameProject":"Tên dự án(*)", "Description":"Mục tiêu dự án(*)", "Budget":"Ngân sách(*)"}
        widgets = {
            'NameProject': forms.TextInput(),
            'Description': forms.Textarea(attrs={'class': 'my-textarea'}),
        }

class EditProjectForm(forms.ModelForm):
    managerChoice = forms.ModelChoiceField(queryset=None, label="Quản lý dự án", empty_label=None)
    def __init__(self, *args, **kwargs):
        choiceMember = kwargs.pop('choices', None)
        oldManager = kwargs.pop('old', None)
        super(EditProjectForm, self).__init__(*args, **kwargs)
        self.fields['managerChoice'].queryset = choiceMember
        self.fields['managerChoice'].initial  = oldManager 
        
    class Meta:
        model = Project
        fields = ["NameProject", "Description", "Budget"]
        labels = {"NameProject":"Tên dự án(*)", "Description":"Mục tiêu dự án(*)", "Budget":"Ngân sách(*)"}
        widgets = {
            'NameProject': forms.TextInput(),
            'Description': forms.Textarea(attrs={'class': 'my-textarea'}),
        }

class ChangePassForm(forms.Form):
    uppercase_validator = RegexValidator(
        regex=r'[A-Z]',
        message="Phải chứa ít nhất một ký tự in hoa.",
        code="no_uppercase"
    )
    number_validator = RegexValidator(
        regex=r'[0-9]',
        message="Phải chứa ít nhất một chữ số.",
        code="no_number"
    )
    special_character_validator = RegexValidator(
        regex=r'[!@#$%^&*(),.?":{}|<>]',
        message="Phải chứa ít nhất một ký tự đặc biệt.",
        code="no_special_character"
    )
    last_password = forms.CharField(max_length=None, label="Mật khẩu hiện tại(*)")
    new_password = forms.CharField(max_length=None, label="Mật khẩu mới(*)", validators=[uppercase_validator, number_validator, special_character_validator])
    re_password = forms.CharField(max_length=None, label="Xác nhận mật khẩu(*)")

class EditAccountForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["Username", "Email", "Avatar"]
        labels = {"Username":"Tên tài khoản(*)", "Avatar":"Ảnh đại diện(*)"}
        widgets = {
            "Username": forms.TextInput(),
            "Email": forms.EmailInput(),
            "Avatar": forms.FileInput(),
        }

    def __init__(self, *args, **kwargs):
        super(EditAccountForm, self).__init__(*args, **kwargs)
        self.fields['Email'].required = False
        self.fields['Avatar'].required = False

class MakePhaseForm(forms.ModelForm):
    class Meta:
        model = Phase
        fields = ["PhaseName", "StartDate", "EndDate"]
        labels = {"PhaseName":"Tên giai đoạn(*)","StartDate":"Ngày bắt đầu(*)", "EndDate":"Ngày kết thúc(*)"}
        widgets = {
            "PhaseName": forms.TextInput(),
            "StartDate": AdminDateWidget(),
            "EndDate": AdminDateWidget(),
        }
    
    def is_dateCorrect(self):
        if self.cleaned_data.get("StartDate") <= self.cleaned_data.get("EndDate"):
            return True
        else:
            return False
        
class MakeTaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ["TaskName", "Description", "Budget", "StartDate", "EndDate"]
        labels = {"TaskName":"Tên nhiệm vụ(*)","Description":"Mô tả(*)", "Budget":"Ngân sách(*)","StartDate":"Ngày bắt đầu(*)", "EndDate":"Ngày kết thúc(*)"}
        widgets = {
            "TaskName": forms.TextInput(),
            "Description": forms.Textarea(attrs={'class': 'my-textarea'}), 
            "StartDate": AdminDateWidget(attrs={'id':'id_taskStartDate'}),
            "EndDate": AdminDateWidget(attrs={'id':'id_taskEndDate'}),
        }
    
    def is_dateCorrect(self):
        if self.cleaned_data.get("StartDate") <= self.cleaned_data.get("EndDate"):
            return True
        else:
            return False
    
    def is_inPhase(self, begin, end):
        if begin <= self.cleaned_data.get("StartDate") and self.cleaned_data.get("EndDate") <= end:
            return True
        else:
            return False

class MakeRepostForm(forms.ModelForm):
    class Meta:
        model = Repost
        fields = ["Description","Result","RealStartDate"]
        labels = {"Description":"Quá trình thực hiện(*)", "Result":"Kết quả(*)","RealStartDate":"Ngày bắt đầu"}
        widgets = {
            'Description': forms.Textarea(attrs={'class': 'my-textarea'}),
            'Result': forms.Textarea(attrs={'class': 'my-textarea'}),
            "RealStartDate": AdminDateWidget()
        }
    
    def is_dateCorrect(self):
        today = datetime.datetime.now().date()
        if self.cleaned_data.get("RealStartDate") <= today:
            return True
        else:
            return False

class ShowRepostForm(forms.ModelForm):
    writer = forms.CharField(label="Người viết báo cáo", disabled=True, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    endDate = forms.CharField(label="Ngày báo cáo", disabled=True, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    class Meta:
        model = Repost
        fields = ["Description", "Result","RealStartDate"]
        labels = {"Description":"Quá trình thực hiện", "Result":"Kết quả","RealStartDate":"Ngày bắt đầu"}
        widgets = {
            'Description': forms.Textarea(attrs={'disabled': 'disabled','class': 'my-textarea'}),
            'Result': forms.Textarea(attrs={'disabled': 'disabled','class': 'my-textarea'}),
            "RealStartDate": forms.TextInput(attrs={'disabled': 'disabled'})
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['writer'].initial = self.instance.Id_writer.Id_user.Username
        self.fields['endDate'].initial = self.instance.DateRepost.strftime("%Y-%m-%d")

class MakeCheckForm(forms.ModelForm):
    class Meta:
        model = Check
        fields = ["Result"]
        labels = {"Result":"Kết quả kiểm tra"}
        widgets = {
            'Result': forms.Textarea(attrs={'class': 'my-textarea'}),
        }

class ReadCheckForm(forms.ModelForm):
    task = forms.CharField(label="Nhiệm vụ kiểm tra", disabled=True, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    writer = forms.CharField(label="Người kiểm tra", disabled=True, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    progress = forms.CharField(label="Tiến độ duyệt", disabled=True, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    class Meta:
        model = Check
        fields = ["Result"]
        labels = {"Result":"Kết quả kiểm tra"}
        widgets = {
            'Result': forms.Textarea(attrs={'disabled': 'disabled','class': 'my-textarea'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['writer'].initial = self.instance.Id_writer.Id_user.Username
        self.fields['task'].initial = self.instance.Id_assign.Id_task.TaskName
        self.fields['progress'].initial = str(self.instance.Progress) + "%"

class MakeProjectRepostForm(forms.ModelForm):
    class Meta:
        model = ProjectRepost
        fields = ["Progress","Risk","Propose"]
        labels = {"Progress":"Tiến trình hiện tại(*)", "Risk":"Rủi ro gặp phải(*)","Propose":"Yêu cầu hỗ trợ(*)"}
        widgets = {
            'Progress': forms.Textarea(attrs={'class': 'my-textarea'}),
            'Risk': forms.Textarea(attrs={'class': 'my-textarea'}),
            'Propose': forms.Textarea(attrs={'class': 'my-textarea'}),
        }

class ReadProjectRepostForm(forms.ModelForm):
    class Meta:
        model = ProjectRepost
        fields = ["Progress","Risk","Propose"]
        labels = {"Progress":"Tiến trình hiện tại", "Risk":"Rủi ro gặp phải","Propose":"Yêu cầu hỗ trợ"}
        widgets = {
            'Progress': forms.Textarea(attrs={'disabled': 'disabled','class': 'my-textarea'}),
            'Risk': forms.Textarea(attrs={'disabled': 'disabled','class': 'my-textarea'}),
            'Propose': forms.Textarea(attrs={'disabled': 'disabled','class': 'my-textarea'}),
        }

class CreateGroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ["GroupName", "MaxNumber"]
        labels = {"GroupName":"Tên nhóm(*)", "MaxNumber":"Số thành viên tối đa"}
        widgets = {
            'GroupName': forms.TextInput(),
        }

class FinishProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ["Result", "Evaluation", "Handover"]
        labels = {"Result":"Kết quả dự án", "Evaluation":"Đánh giá sản phẩm", "Handover":"Bàn giao sản phẩm"}
        widgets = {
            'Result': forms.Textarea(attrs={'class': 'my-textarea'}),
            'Evaluation': forms.Textarea(attrs={'class': 'my-textarea'}),
            'Handover': forms.Textarea(attrs={'class': 'my-textarea'}),
        }

class ShowFinishProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ["NameProject", "Description", "Result", "Evaluation", "Handover"]
        labels = {"NameProject":"Tên dự án", "Description":"Mục tiêu dự án", "Result":"Kết quả dự án", "Evaluation":"Đánh giá sản phẩm", "Handover":"Bàn giao sản phẩm"}
        widgets = {
            'NameProject': forms.TextInput(attrs={'disabled': 'disabled'}),
            'Description': forms.Textarea(attrs={'disabled': 'disabled','class': 'my-textarea'}),
            'Result': forms.Textarea(attrs={'disabled': 'disabled','class': 'my-textarea'}),
            'Evaluation': forms.Textarea(attrs={'disabled': 'disabled','class': 'my-textarea'}),
            'Handover': forms.Textarea(attrs={'disabled': 'disabled','class': 'my-textarea'}),
        }
