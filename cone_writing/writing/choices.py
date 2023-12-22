from django.db.models import IntegerChoices, TextChoices
from urllib.parse import urlparse


class WritingStatus(IntegerChoices):
    OK = 1, '正常'
    DELETED = 2, '已删除'


class MediaType(IntegerChoices):
    AUTO = 1, '自动检测'
    IMAGE = 2, '图片'
    VIDEO = 3, '视频'
    AUDIO = 4, '音频'
    OTHER = 5, '其他'

    @classmethod
    def detect(cls, value: str):
        path = urlparse(value).path.lower()
        for suffix in ['jpg', 'png', 'jpeg', 'gif', 'bmp', 'tif']:
            if path.endswith(suffix):
                return cls.IMAGE
        return cls.OTHER


class MediaEngine(IntegerChoices):
    QINIU = 1, '七牛云'
    LOCAL = 2, '本地'


class MediaModel(TextChoices):
    MOMENT = 'Moment', '动态'
