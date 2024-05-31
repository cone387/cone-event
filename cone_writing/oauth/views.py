import json
import os
from datetime import datetime
from django.contrib.auth import get_user_model
from rest_framework.generics import RetrieveAPIView
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken
from django.shortcuts import redirect
from urllib.parse import urlparse
from django.conf import settings
from .models import OauthUser
from .choices import OauthPlatform
import time
import base64
import hmac
import requests
import hashlib

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['username', 'email', 'is_staff', 'is_active', 'date_joined', 'last_login', 'is_superuser']


class UserView(RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.user


class DingDingOauthView(APIView):
    # https://login.dingtalk.com/oauth2/auth?redirect_uri=https://2ffa624b.r12.cpolar.top/oauth/dingding/callback/&response_type=code&client_id=dingxrqql5qmkr8iszsc&scope=openid&state=dddd&prompt=consent
    # https://oapi.dingtalk.com/connect/oauth2/sns_authorize?appid=dingxrqql5qmkr8iszsc&response_type=code&scope=snsapi_login&state=STATE&redirect_uri=https://2ffa624b.r12.cpolar.top/oauth/dingding/callback/
    headers = {'Content-Type': 'application/json'}
    renderer_classes = (TemplateHTMLRenderer, )
    platform = OauthPlatform.DINGDING

    def __init__(self):
        super().__init__()
        self.client_id = getattr(settings, 'DD_OAUTH_CLIENT_ID', None) or os.environ['DD_OAUTH_CLIENT_ID']
        self.client_secret = getattr(settings, 'DD_OAUTH_CLIENT_SECRET', None) or os.environ['DD_OAUTH_CLIENT_SECRET']

    def get_access_token(self, code, grantType="authorization_code"):
        data = {
          "clientId": self.client_id,
          "clientSecret": self.client_secret,
          "code": code,
          # "refreshToken": "",
          "grantType": grantType
        }
        response = requests.post(
            'https://api.dingtalk.com/v1.0/oauth2/userAccessToken',
            headers=self.headers,
            json=data
        )
        if response.status_code != 200:
            raise AuthenticationFailed("请求access token失败")
        result = response.json()
        if not result.get('accessToken'):
            raise AuthenticationFailed("accessToken没找到")
        return result

    def get_access_info(self, code):
        token_result = self.get_access_token(code)
        headers = self.headers.copy()
        headers['x-acs-dingtalk-access-token'] = token_result['accessToken']
        response = requests.get(
            'https://api.dingtalk.com/v1.0/contact/users/me',
            headers=headers
        )
        if response.status_code != 200:
            raise AuthenticationFailed("获取用户信息错误")
        result = response.json()
        if not result.get('openId'):
            raise AuthenticationFailed("openid not found")
        result['token'] = token_result
        return result

    # 手机端授权，从钉钉内部登录
    def get_access_info_of_sns(self, code):
        # 时间戳
        timestamp = str(int(time.time() * 1000))
        signature = base64.b64encode(
            hmac.new(self.client_secret.encode(), timestamp.encode(), digestmod=hashlib.sha256).digest()).decode()
        res = requests.post('https://oapi.dingtalk.com/sns/getuserinfo_bycode',
                            params={
                                'signature': signature,
                                "timestamp": timestamp,
                                "accessKey": self.client_id,
                            }, json={"tmp_auth_code": code}, headers=self.headers)
        '''
            nick: 用户在钉钉上面的昵称。
            unionid: 用户在当前开放应用所属企业的唯一标识。
            openid: 用户在当前开放应用内的唯一标识。
            main_org_auth_high_level: 用户主企业是否达到高级认证级别。
        '''
        return res.json()

    def get(self, request):
        code, state = request.query_params.get('code'), request.query_params.get('state', '')
        redirect_url = request.query_params.get('redirect', '/')
        parsed = urlparse(redirect_url)
        ALLOWED_AUTH_HOSTS = getattr(settings, 'ALLOWED_AUTH_HOSTS', [])
        if parsed.hostname not in ALLOWED_AUTH_HOSTS:
            raise AuthenticationFailed("不允许的重定向")
        access_info = self.get_access_info(code)
        if not access_info:
            raise AuthenticationFailed({"error": "access token not found"})
        # {'nick': 'xxx', 'unionId': 'xxx', 'openId': 'xxx', 'mobile': 'xxx', 'stateCode': '86'}
        name, openId = access_info['nick'], access_info['openId']
        try:
            oauth_user = OauthUser.objects.get(oauth_id=openId)
            oauth_user.oauth_detail = access_info
            oauth_user.oauth_name = name
            user = oauth_user.user
        except OauthUser.DoesNotExist:
            user = User(username=name, is_active=True, is_staff=True)
            user.set_password(openId)
            user.save()
            oauth_user = OauthUser.objects.create(oauth_id=openId, oauth_detail=access_info, oauth_name=name,
                                                  user=user)
        oauth_user.save()
        user.last_login = datetime.now()
        user.save()
        refresh = RefreshToken.for_user(user)
        access = json.dumps({
            "refresh": str(refresh),
            "access": str(refresh.access_token)
        })
        access = base64.b64encode(access.encode()).decode()
        redirect_url += f'{"&" if "?" in redirect_url else "?"}access={access}'
        return redirect(redirect_url)
