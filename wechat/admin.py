from django.contrib import admin
from .models import WxUser
# Register your models here.
class WxUserAdmin(admin.ModelAdmin):
    list_display = ('owner', 'openid', 'name', 'login',
                    'session', 'other', 'createtime', )
    search_fields = ('name',)
admin.site.register(WxUser, WxUserAdmin)
