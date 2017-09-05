from django.contrib import admin
from django.utils import simplejson as json
from django.utils.translation import ugettext_lazy as _
from models import *

class NoticeshipInline(admin.TabularInline):
    classes = ('grp-collapse grp-open',)
    model = Noticeship
    fields = ('notice', 'position')
    sortable_field_name = 'position'
    raw_id_fields = ('notice', )
    related_lookup_fields = {
        'fk': ('notice',)
    }
    extra = 0

class ZoneAdmin(admin.ModelAdmin):
    inlines = (NoticeshipInline, )
    list_display = ('zoneid', 'domain', 'maxnum', 'status', 'index')
    search_fields = ('zoneid', 'domain')
    fields = ('zoneid', 'domain', 'maxnum', 'channels', 'status', 'index')
    filter_vertical = ('channels', )

class ChannelAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'version', 'version2', 'version3')
    search_fields = ('title', 'version')
    fields = ('title', 'slug', 'version', 'version2', 'version3')

class NoticeAdmin(admin.ModelAdmin):
    list_display = ('title', 'content', 'created_at', 'sign')
    search_fields = ('title', )
    fields = ('title', 'content', 'screenshot', 'created_at', 'sign', )

class UpdateAdmin(admin.ModelAdmin):
    list_display = ('channel', 'url', 'cversion', 'tversion', 'sign')
    search_fields = ('cversion', 'tversion')
    fields = ('channel', 'url', 'cversion', 'tversion', 'sign')

class UpgradeAdmin(admin.ModelAdmin):
    list_display = ('channel', 'version', 'url', 'md5')
    search_fields = ('version', 'url')
    fields = ('channel', 'version', 'url', 'md5')

class CodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'created_at', 'ended_at', 'gold', 'rock', 'feat', 'hp', 'prods', 'nums')
    search_fields = ('code', )
    fields =('code', 'created_at', 'ended_at', 'gold', 'rock', 'feat', 'hp', 'prods', 'nums', 'channels')
    filter_vertical = ('channels', )

class UserCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'user_id', 'zone_id', 'channel')
    search_fields = ('code', 'user_id')
    fields =('code', 'user_id', 'zone_id', 'channel')

# class ZoneshipInline(admin.TabularInline):
#     classes = ('grp-collapse grp-open',)
#     model = Zoneship
#     fields = ('zone', 'position')
#     #raw_id_fields = ('zone', )
#     # related_lookup_fields = {
#     #     'fk': ('zone',)
#     # }
#     extra = 0

# class BigEventAdmin(admin.ModelAdmin):
#     #inlines = (ZoneshipInline, )
#     list_display = ('bid', 'name', 'index', 'type', 'created_at', 'ended_at')
#     search_fields = ('bid', 'name')
#     fields = ('bid', 'name', 'index', 'type', 'channels', 'created_at', 'ended_at')
#     filter_vertical = ('channels', )

class MailLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'zid', 'mail', 'created_at')
    search_fields = ('user__username', 'zid', 'created_at')
    fields = ('user', 'mail', 'created_at')
    list_filter = ('user', 'zid', 'created_at')

admin.site.register(Zone, ZoneAdmin)
admin.site.register(Channel, ChannelAdmin)
admin.site.register(Notice, NoticeAdmin)
admin.site.register(Update, UpdateAdmin)
admin.site.register(Upgrade, UpgradeAdmin)
admin.site.register(Code, CodeAdmin)
admin.site.register(UserCode, UserCodeAdmin)
#admin.site.register(BigEvent, BigEventAdmin)
admin.site.register(MailLog, MailLogAdmin)