from django.conf.urls import include, url

from . import views

urlpatterns = [
    #服务器认证
    url(r'^$', views.index.as_view(),
    url(r'^auth$', views.wxAuth.as_view()),
    url(r'^normalauth$', views.WxAuthUserName.as_view()),
    url(r'^webauth$', views.webAuth.as_view()),
]
