# -*- coding:utf-8 -*-

# author: Cone
# datetime: 2021-02-22 17:29
# software: PyCharm
import re
from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.request import Request
from urllib.parse import urlparse
from utils import qiniu_cloud
from . import models
from .choices import MediaType

medias_compiler = re.compile(r'!\[.*?\]\((.*?)\)')

UserModel = get_user_model()


def convert_delta_medias(delta, media_values=[], media_keys=['image', 'video'],):
    if isinstance(delta, dict):
        for k, v in delta.items():
            if k in media_keys and not v.startswith('http'):
                value = media_values.pop()
                delta[k] = value
            else:
                convert_delta_medias(v, media_keys, media_values)
    elif isinstance(delta, list):
        for o in delta:
            convert_delta_medias(o, media_keys, media_values)
    return delta


# def process_media(media, serializer: serializers.ModelSerializer):
#     if media:
#         return SeemeImage.objects.create(
#             media=media,
#             create_by=serializer.validated_data.get('create_by', serializer.Meta.model._meta.label),
#             user=serializer.context['request'].user)
#
#
# def process_medias(medias, serializer: serializers.ModelSerializer):
#     return [
#         process_media(x, serializer)
#         for x in medias
#     ]


class MediaFileFiled(serializers.FileField):

    def to_representation(self, value):
        value = super(MediaFileFiled, self).to_representation(value)
        if value:
            value = qiniu_cloud.auth.private_download_url(value)
        return value


class MediaSerializer(serializers.ModelSerializer):
    size = serializers.IntegerField(required=False, label="大小")
    upload_time = serializers.DateTimeField(read_only=True)
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    uri = MediaFileFiled(
        max_length=100000, allow_empty_file=False, allow_null=False,
        use_url=True, required=False, label="媒体文件(可选)",
    )
    url = serializers.CharField(required=False, allow_null=False, label="自定义地址(可选)")

    class Meta:
        model = models.Media
        exclude = ['create_time', 'update_time']

    def save(self, **kwargs):
        uri = self.validated_data.get('uri')
        url: str = self.validated_data.pop('url', None)
        size = self.validated_data.pop('size', None)
        media_type = self.validated_data.get('type', None)
        engine = self.validated_data.get('engine', None)
        if (uri and url) or not (uri or url):
            raise serializers.ValidationError({"uri|url": "uri和url必须且只能存在一个"})
        if not media_type or media_type == MediaType.AUTO:
            self.validated_data['type'] = MediaType.detect(url)
        if url:
            storage = models.get_file_storage(engine)
            if url.startswith('http://cdn.cone387.top/'):
                self.validated_data['uri'] = urlparse(url).path[1:]
            else:
                try:
                    self.validated_data['uri'] = storage.fetch(url)
                except Exception as e:
                    raise serializers.ValidationError({"url": str(e)})
                size = self.validated_data['uri'].size
        else:
            size = uri.size
        super(MediaSerializer, self).save(size=size, **kwargs)


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserModel
        fields = ['username', 'email', 'is_staff', 'is_active', 'date_joined', 'last_login', 'is_superuser']


class TagSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = models.Tag
        exclude = ("update_time", "create_time")


class FeelingSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = models.Feeling
        exclude = ['create_time']


class WritingSerializer(serializers.ModelSerializer):
    create_time = None
    update_time = None
    extra = serializers.JSONField(default={}, required=False, allow_null=True, label="其他")
    tags = TagSerializer(many=True, required=False, read_only=True)
    post_tags = serializers.CharField(write_only=True, allow_null=True, allow_blank=True,
                                      help_text='标签, 按逗号分隔, 例如: 标签1, 标签2, 标签3',
                                      required=False, label='标签')
    # medias = serializers.ListField(
    #     required=False,
    #     child=serializers.FileField(
    #         max_length=100000, allow_empty_file=False,
    #         use_url=True), write_only=True, allow_null=True
    # )
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    def save(self, **kwargs):
        # delta = self.validated_data.get('delta', None)
        # if delta:
        #     uploaded_medias: List[SeemeImage] = process_medias(self.validated_data.pop('medias', []), self)
        #     convert_delta_medias(delta, media_values=[x.media.url for x in uploaded_medias])
        request: Request = self.context['request']
        ip = request.META.get('HTTP_X_FORWARDED_FOR') or request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT')
        extra = self.validated_data.pop('extra', None) or kwargs.pop('extra', None) or {}
        extra['device'] = {
            'ip': ip,
            'ua': user_agent
        }
        return super().save(extra=extra, **kwargs)

    def create(self, validated_data):
        post_tags: str = validated_data.pop('post_tags', None)
        instance = super(WritingSerializer, self).create(validated_data)
        if post_tags and post_tags.strip():
            tags = []
            for tag in post_tags.split(','):
                tag = tag.strip().capitalize()
                tag, created = models.Tag.objects.get_or_create(name=tag, user=self.context['request'].user)
                tags.append(tag)
            instance.tags.set(tags)
        return instance

    def update(self, instance: models.Writing, validated_data):
        tags = validated_data.pop('post_tags', [])
        if tags:
            instance.tags.clear()
        for tag in tags:
            tag, created = models.Tag.objects.get_or_create(name=tag, user=self.context['request'].user)
            instance.tags.add(tag)
        return super().update(instance, validated_data)


class FeelingPostSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Feeling
        exclude = ['update_time', 'user', 'create_time']


class MomentSerializer(WritingSerializer):
    feeling = FeelingSerializer(read_only=True)
    post_feeling = serializers.PrimaryKeyRelatedField(
        source='feeling', write_only=True, allow_null=True, required=False, label='心情',
        queryset=models.Feeling.objects.all())
    medias = MediaSerializer(many=True, read_only=True)
    post_medias = serializers.PrimaryKeyRelatedField(
        source='medias', queryset=models.Media.objects.all(),
        many=True, write_only=True, allow_null=True, required=False, label='媒体')

    def create(self, validated_data):
        medias = validated_data.get('medias')
        if medias:
            validated_data['media_info'] = [x.id for x in medias]
        return super().create(validated_data)

    class Meta:
        model = models.Moment
        exclude = ['update_time', 'writing_status']


class ThingSerializer(serializers.ModelSerializer):
    feeling = FeelingSerializer(read_only=True)
    feeling_id = serializers.PrimaryKeyRelatedField(
        source='feeling', write_only=True, allow_null=True, required=False, label='心情',
        queryset=models.Feeling.objects.all())

    parent = serializers.SerializerMethodField()

    def get_parent(self, obj: models.Thing):
        if obj.parent:
            return self.__class__(obj.parent).data

    class Meta:
        model = models.Thing
        exclude = ['update_time', 'user']


class FeelingRecordSerializer(serializers.ModelSerializer):
    feeling = FeelingSerializer(read_only=True)
    feeling_id = serializers.PrimaryKeyRelatedField(
        source='feeling', write_only=True, allow_null=True, required=False, label='心情',
        queryset=models.Feeling.objects.all())

    thing = ThingSerializer(read_only=True)
    thing_id = serializers.PrimaryKeyRelatedField(
        source='thing', write_only=True, allow_null=True, required=False, label='事情',
        queryset=models.Thing.objects.all())

    moment = MomentSerializer(read_only=True)
    moment_id = serializers.PrimaryKeyRelatedField(
        source='moment', write_only=True, allow_null=True, required=False, label='瞬间',
        queryset=models.Moment.objects.all())

    class Meta:
        model = models.FeelingRecord
        exclude = ['update_time']
