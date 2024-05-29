from django.contrib import admin
from .models import *
from .supposter import *
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
# Register your models here.

class UserDisplay_Admin(admin.ModelAdmin):
    list_display = ("Id_user", "Username", "Email","image_display", "Online", "Lock")
    search_fields = ("Id_user", "Username", "Email",)
    readonly_fields = ("Spice", "EncodePass", "Avatar")

    def reset_password(self, request, queryset):
        for obj in queryset:
            password = "123@Abc"
            obj.Spice = randomString(10)
            obj.EncodePass = encodePassword(obj.Spice, password)
            obj.save()

    def lock_user(self, request, queryset):
        for obj in queryset:
            obj.Lock = True
            obj.save()
    
    def unlock_user(self, request, queryset):
        for obj in queryset:
            obj.Lock = False
            obj.save()
    
    def image_display(self, obj):
        return mark_safe(f'<img src="{obj.Avatar.url}" style="max-width: 100px; max-height: 100px;" />')

    image_display.allow_tags = True
    image_display.short_description = 'Image'

    reset_password.short_description = "Đặt lại mật khẩu"
    lock_user.short_description = "Khóa tài khoản"
    unlock_user.short_description = "Mở khóa tài khoản"

    actions = [reset_password, lock_user, unlock_user]

admin.site.register(User, UserDisplay_Admin)

class ProjectDisplay_Admin(admin.ModelAdmin):
    list_display = ("Id_project", "NameProject", "Description","Budget","Finished")
    search_fields = ("Id_project", "NameProject")
admin.site.register(Project, ProjectDisplay_Admin)

class SupportChatAdmin(admin.ModelAdmin):
    list_display = ('username', 'user_id', 'chat_button')
    def chat_button(self, obj):
        url = reverse('support page', args=['a',obj.pk])
        return format_html('<a class="button" href="{}">Chat</a>', url)
    
    def user_id(self, obj):
        return obj.Id_user.pk
    
    def username(self, obj):
        return obj.Id_user.Username
    
    chat_button.short_description = 'Chat'

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_chat_button'] = True
        return super().change_view(request, object_id, form_url, extra_context=extra_context)
    
admin.site.register(SupportChat, SupportChatAdmin)

class RepostAdmin(admin.ModelAdmin):
    list_display = ('Id_repost', 'DateRepost')

admin.site.register(Repost, RepostAdmin)

class ProjectRepostAdmin(admin.ModelAdmin):
    list_display = ('Id_repost', 'Id_project', 'DateRepost')

admin.site.register(ProjectRepost, ProjectRepostAdmin)

class SharingFileAdmin(admin.ModelAdmin):
    list_display = ('Id_project', 'Id_member_share', 'FileName', 'UploadDate')

admin.site.register(SharingFile, SharingFileAdmin)