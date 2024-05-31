from django.contrib import admin
from . import models
# Register your models here.


class OauthUserAdmin(admin.ModelAdmin):

    list_display = ('id', 'user', 'platform', 'oauth_name', 'update_time')
    readonly_fields = ('create_time', 'update_time', 'oauth_detail')

    fields = (
        'user',
        ('oauth_id', 'oauth_name'),
        'oauth_detail',
        ('create_time', 'update_time')
    )


admin.site.register(models.OauthUser, OauthUserAdmin)
