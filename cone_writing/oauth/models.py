from django.contrib.auth import get_user_model
from django.db import models
from .choices import OauthPlatform
# Create your models here.


User = get_user_model()


class OauthUser(models.Model):
    platform = models.TextField(max_length=20, default=OauthPlatform.DINGDING, choices=OauthPlatform.choices,
                                verbose_name='平台')
    user = models.ForeignKey(User, db_constraint=False, on_delete=models.CASCADE, verbose_name='用户')
    oauth_id = models.CharField(max_length=100, verbose_name='Oauth用户ID')
    oauth_name = models.CharField(max_length=100, verbose_name='Oauth用户名', null=True, blank=True)
    oauth_detail = models.JSONField(verbose_name='授权信息')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'oauth_user'
        verbose_name = verbose_name_plural = 'Oauth用户'

    def __str__(self):
        return self.oauth_name
