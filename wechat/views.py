import datetime
import json
import hashlib
import requests
import random
import string
from django.contrib.auth.models import User
from django.shortcuts import render
from django.http.response import HttpResponse
from django.contrib.auth import authenticate
from rest_framework.views import APIView, Response
from django.views import View
from django.core.cache import cache
from rest_framework_jwt.settings import api_settings
from midd.views import AddActionLog, SerializerRespons
from .models import WxUser

jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER


Wx_APPSecretKey = ""
Wx_APPID = ""

# 基础授权部分
#=================================================
#小程序授权API
Wx_API = "https://api.weixin.qq.com/sns/jscode2session?appid={appid}&secret={appsecret}&js_code={code}&grant_type=authorization_code"
#jsAPI
get_access_token_api = 'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=%s&secret=%s'
get_ticket = 'https://api.weixin.qq.com/cgi-bin/ticket/getticket?type=jsapi&access_token='
#微信110
wx_110="https://weixin110.qq.com/cgi-bin/mmspamsupport-bin/newredirectconfirmcgi?main_type=2&evil_type=43&source=2&url={url}&exportkey=&pass_ticket=a&wechat_real_lang=zh_CN"
#=================================================


# 用于微信接口验证
class index(View):
    def get(self, request, *args, **kwargs):
        signature = request.GET.get('signature', None)
        timestamp = request.GET.get('timestamp', None)
        nonce = request.GET.get('nonce', None)
        echostr = request.GET.get('echostr', None)
        # 服务器配置中的token
        token =Wx_token
        # 把参数放到list中排序后合成一个字符串，再用sha1加密得到新的字符串与微信发来的signature对比，如果相同就返回echostr给服务器，校验通过
        hashlist = [token, timestamp, nonce]
        hashlist.sort()
        hashstr = ''.join([s for s in hashlist])
        hashstr = hashlib.sha1(hashstr.encode()).hexdigest()
        if hashstr == signature:
            return HttpResponse(echostr)
        else:
            return HttpResponse("field")
    # 服务号接口的主要接口
    def post(self, requst):
        othercontent = autoreply(requst)
        return HttpResponse(othercontent)



class base_authorization():
    @classmethod
    def get_ticket(cls,appid,appsecret):
        key = 'ticket'
        if cache.has_key(key):
            ticket = cache.get(key)
        else:
            if cache.has_key('access_token'):
                access_token = cache.get('access_token')
            else:
                access_token = cls.get_access_token(appid,appsecret)
            ticket = requests.get(get_ticket+access_token).json()['ticket']
            cache.set(key, ticket, 110*60)
        return ticket

    @staticmethod
    def get_access_token(appid,appsecret):
        key = 'access_token'
        access_token = requests.get(get_access_token_api % (appid,appsecret)).json()['access_token']
        cache.set(key, access_token, 110*60)
        return access_token

# 签名算法
class signature():
    def __init__(self, url,appid,appsecret):
        self.ret = {
            'nonceStr': self.__create_nonce_str(),
            'jsapi_ticket': base_authorization.get_ticket(appid,appsecret),
            'timestamp': self.__create_timestamp(),
            'url': url,
        }

    def __create_nonce_str(self):
        return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(15))

    def __create_timestamp(self):
        return int(time.time())

    def sign(self):
        string = '&'.join(['%s=%s' % (key.lower(), self.ret[key])
                           for key in sorted(self.ret)]).encode('utf-8')
        self.ret['signature'] = hashlib.sha1(string).hexdigest()
        return self.ret


'''
jssdk签名接口
'''

class webAuth(View):
    def __init__(self,apilist):
        self.apps=['showMenuItems', 'onMenuShareTimeline','onMenuShareAppMessage',]
        return super().__init__(self)

    def post(self, request, *args, **kwargs):
        request_type = request.POST.get('type')
        if not request_type:
            # request_body = json.loads(request.body.decode())
            pathname = request.POST.get('url')
            sign = signature(str(pathname))
            signs=sign.sign()
            signs['appId']=Wx_APPID
            signs['jsApiList']=self.apps
            sign = json.dumps(signs)
            return HttpResponse(sign, content_type="application/json")
        elif request_type == 'image/jpeg':
            pass  # 传图片的时候会用到



# -----------小程序------------------------------------------------
'''
用openid登陆,没有关联用户就增加用户
===请求参数
{
    "code":"小程序登陆code",
}
'''


class wxAuth(APIView):
    @classmethod
    def GetWxApi(self,code):
        return Wx_API.format(appid=Wx_APPID, appsecret=Wx_APPSecretKey, code=code)
    def post(self, request):
        data = request.data
        if "code" in data.keys():
            wxapi = self.GetWxApi(data["code"])
            api_context = json.loads(requests.get(wxapi).text)
            if "openid" in api_context.keys():
                # 正确登陆
                try:
                    wxu = WxUser.objects.get(openid=api_context['openid'])
                    u = wxu.owner
                    wxu.session = api_context['session_key']
                    wxu.save()
                    payload = jwt_payload_handler(u)
                    token = jwt_encode_handler(payload)
                    return Response(SerializerRespons("success", "登陆成功", {"token": token}))
                except:  # 如果没哟账户关联,直接返回
                    username = "wx" + datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")
                    u = User(username=username)
                    u.set_password("111111")
                    u.save()
                    wxu = WxUser(
                        owner=u,
                        openid=api_context['openid'],
                        session=api_context['session_key'],
                        login=1,
                        name=data['name'])
                    wxu.save()
                    payload = jwt_payload_handler(u)
                    token = jwt_encode_handler(payload)
                    return Response(SerializerRespons("errors", "1000", "登陆失败,无此用户"))
            else:
                # 错误登陆
                return Response(SerializerRespons("errors", "1001", "参数不正确"))


'''
用户名密码认证

===请求参数
{
    "code":"小程序登陆code",
    "username":"用户名",
    "password":"密码"
    "nickname":"微信昵称"
}
'''


class WxAuthUserName(APIView):
    def post(self, request):
        data = request.data
        wxapi = GetWxApi(data["code"])
        api_context = json.loads(requests.get(wxapi).text)
        if "openid" in api_context.keys():
            user = authenticate(
                username=data['username'], password=data['password'])
            if user is not None:
                wxu = WxUser(
                    owner=user,
                    openid=api_context['openid'],
                    session=api_context['session_key'],
                    login=1,
                    name=data['nickname'])
                wxu.save()
                payload = jwt_payload_handler(user)
                token = jwt_encode_handler(payload)
                return Response(SerializerRespons("success", "登陆成功", {"token": token}))
            else:
                return Response(SerializerRespons("errors", "1000", "登陆失败,无此用户"))
        else:
            # 错误登陆
            return Response(SerializerRespons("errors", "1001", "参数不正确"))


# --自动回复代码片段------
import xml.etree.ElementTree as ET
def autoreply(request):
    try:
        webData = request.body
        xmlData = ET.fromstring(webData)
        msg_type = xmlData.find('MsgType').text
        ToUserName = xmlData.find('ToUserName').text
        FromUserName = xmlData.find('FromUserName').text
        CreateTime = xmlData.find('CreateTime').text
        MsgType = xmlData.find('MsgType').text
        MsgId = xmlData.find('MsgId').text

        toUser = FromUserName
        fromUser = ToUserName

        if msg_type == 'text':
            content = "您好,欢迎来到Python大学习!希望我们可以一起进步!"
            replyMsg = TextMsg(toUser, fromUser, content)
            return replyMsg.send()

        elif msg_type == 'image':
            content = "图片已收到,谢谢"
            replyMsg = TextMsg(toUser, fromUser, content)
            return replyMsg.send()
        elif msg_type == 'voice':
            content = "语音已收到,谢谢"
            replyMsg = TextMsg(toUser, fromUser, content)
            return replyMsg.send()
        elif msg_type == 'video':
            content = "视频已收到,谢谢"
            replyMsg = TextMsg(toUser, fromUser, content)
            return replyMsg.send()
        elif msg_type == 'shortvideo':
            content = "小视频已收到,谢谢"
            replyMsg = TextMsg(toUser, fromUser, content)
            return replyMsg.send()
        elif msg_type == 'location':
            content = "位置已收到,谢谢"
            replyMsg = TextMsg(toUser, fromUser, content)
            return replyMsg.send()
        else:
            msg_type == 'link'
            content = "链接已收到,谢谢"
            replyMsg = TextMsg(toUser, fromUser, content)
            return replyMsg.send()

    except Exception as Argment:
        return Argment


class Msg(object):
    def __init__(self, xmlData):
        self.ToUserName = xmlData.find('ToUserName').text
        self.FromUserName = xmlData.find('FromUserName').text
        self.CreateTime = xmlData.find('CreateTime').text
        self.MsgType = xmlData.find('MsgType').text
        self.MsgId = xmlData.find('MsgId').text


import time


class TextMsg(Msg):
    def __init__(self, toUserName, fromUserName, content):
        self.__dict = dict()
        self.__dict['ToUserName'] = toUserName
        self.__dict['FromUserName'] = fromUserName
        self.__dict['CreateTime'] = int(time.time())
        self.__dict['Content'] = content

    def send(self):
        XmlForm = """
        <xml>
        <ToUserName><![CDATA[{ToUserName}]]></ToUserName>
        <FromUserName><![CDATA[{FromUserName}]]></FromUserName>
        <CreateTime>{CreateTime}</CreateTime>
        <MsgType><![CDATA[text]]></MsgType>
        <Content><![CDATA[{Content}]]></Content>
        </xml>
        """
        return XmlForm.format(**self.__dict)
