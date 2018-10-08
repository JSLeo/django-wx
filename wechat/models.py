from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class WxUser(models.Model):
    owner = models.OneToOneField(User, on_delete=models.CASCADE)
    openid = models.CharField(
        max_length=100,
        verbose_name=u"微信小程序内的id",
        blank=False, null=False,
        primary_key=True)
    name = models.CharField(
        max_length=100, verbose_name=u"微信用户名", blank=True, null=True)
    login = models.BooleanField(verbose_name="登陆状态")
    session = models.CharField(
        max_length=150, verbose_name=u"sessionkey", blank=True, null=True)
    other = models.CharField(
        max_length=250, verbose_name=u"openid", blank=True, null=True)
    createtime = models.DateTimeField(auto_now=True)
    objects = models.Manager()

    def __str__(self):
        return str(self.owner)

    class Meta:
        managed = True
        verbose_name = '用户基础信息'
        verbose_name_plural = '用户基础信息'
