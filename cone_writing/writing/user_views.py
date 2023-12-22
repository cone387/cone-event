# -*- coding:utf-8 -*-

# author: Cone
# datetime: 2020-11-26 12:32
# software: PyCharm
from rest_framework.viewsets import GenericViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework import mixins
from django.contrib.auth import get_user_model
from . import serializers

UserModel = get_user_model()


class UserView(mixins.RetrieveModelMixin, GenericViewSet):
    queryset = UserModel.objects.all()
    serializer_class = serializers.UserSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.user
    #
    # @staticmethod
    # @csrf_exempt
    # @api_view(http_method_names=["POST"])
    # def register(request):
    #     serializer = serializers.UserCreateSerializer(data=request.data)
    #     if not serializer.is_valid():
    #         return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)
    #     user = serializer.save()
    #     data = serializers.UserSerializer(instance=user).data
    #     if getattr(user, 'require_verify', None):
    #         data['require_verify'] = True
    #         data['msg'] = "we have send a verify code to your mail %s" % user.email
    #         return Response(data, status=status.HTTP_202_ACCEPTED)
    #     return Response(data, status.HTTP_201_CREATED)
