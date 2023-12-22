from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone
from django.db.models.fields.files import FieldFile
from .choices import WritingStatus, MediaType, MediaEngine, MediaModel
from .storage import QiniuPrivateStorage, LocalStorage


UserModel = get_user_model()

__all__ = [
    'Moment', 'Feeling', 'Tag', 'Media', 'Writing'
]


def get_file_storage(engine=None):
    if engine == MediaEngine.LOCAL:
        return LocalStorage()
    else:
        return QiniuPrivateStorage()


class MediaFileFiledFile(FieldFile):
    def __init__(self, instance: 'Media', field, name):
        super(MediaFileFiledFile, self).__init__(instance, field, name)
        self.storage = get_file_storage(instance.engine)


class MediaFileFiled(models.FileField):
    attr_class = MediaFileFiledFile

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, storage=QiniuStorage(), **kwargs)

    # def save_form_data(self, instance, data):
    #     if data is not None:
    #         self.storage.engine = instance.engine
    #         setattr(instance, self.name, data)
    #         instance.size = data.size

    # def pre_save(self, model_instance: 'Media', add):
    #     if model_instance.engine == MediaEngine.QINIU:
    #         storage = QiniuStorage()
    #     else:
    #         storage = FileSystemStorage()
    #     self.storage = storage
    #     file = super().pre_save(model_instance, add)
    #     return file


def upload_to(instance: 'Media', filename: str):
    return 'writing/%s/%s/%s' % (
        str(instance.model).lower(), instance.user_id,
        (timezone.now().strftime('%Y%m%d%H%M%S%f') + "." + filename.rsplit('.', 1)[1]) if '.' in filename else ''
    )


class Media(models.Model):
    type = models.IntegerField(verbose_name='类型', choices=MediaType.choices, default=MediaType.AUTO)
    uri = MediaFileFiled(verbose_name='媒体文件', upload_to=upload_to)
    size = models.PositiveIntegerField(verbose_name='大小(Bytes)', default=0)
    model = models.CharField(max_length=20, verbose_name='所属模型', default=MediaModel.MOMENT, choices=MediaModel.choices)
    upload_time = models.DateTimeField(default=timezone.now, verbose_name='上传时间')
    extra = models.JSONField(default=dict, verbose_name='其他信息', null=True, blank=True)
    engine = models.IntegerField(verbose_name='存储引擎', choices=MediaEngine.choices, default=MediaEngine.QINIU)
    user = models.ForeignKey(UserModel, on_delete=models.DO_NOTHING, db_constraint=False, verbose_name='用户')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'user_media'
        verbose_name_plural = verbose_name = '媒体'
        ordering = ['-id']

    def __str__(self):
        return self.uri.name


class Tag(models.Model):
    name = models.CharField(max_length=10, verbose_name='标签名')
    color = models.CharField(max_length=32, null=True, blank=True, verbose_name='颜色')  # default='#ffffff'但不要存入数据库
    user = models.ForeignKey(UserModel, on_delete=models.DO_NOTHING, db_constraint=False, verbose_name='用户')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'user_tag'
        ordering = ['-id']
        unique_together = ('name', 'user')
        verbose_name_plural = verbose_name = '标签'


class Writing(models.Model):
    """
        每个Writing应该包含的基础字段
        1.删除事件不会真的删除，只会将status置为2
        2. extra字段用于存储其他信息, 比如
        {
            "location": 位置信息,
            "device": 设备信息,
            "weather": 天气信息,
        }
    """
    writing_status = models.PositiveIntegerField(choices=WritingStatus.choices, verbose_name='写作状态',
                                                 default=WritingStatus.OK)
    tags = models.ManyToManyField(Tag, blank=True, verbose_name='标签', db_constraint=False)
    medias = models.ManyToManyField(Media, blank=True, verbose_name='媒体', db_constraint=False)
    # ManyToManyField不会字段，只会创建一个中间表，所以新建一个media_info字段用于存储媒体信息
    media_info = models.JSONField(default=list, blank=True, verbose_name='媒体信息', null=True)
    extra = models.JSONField(default=dict, blank=True, verbose_name='其他信息')
    user = models.ForeignKey(UserModel, on_delete=models.DO_NOTHING, db_constraint=False, verbose_name='用户')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间', db_index=True)
    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        abstract = True


class Feeling(models.Model):
    emoji = models.CharField(max_length=30, verbose_name='emoji', unique=True)
    name = models.CharField(max_length=30, verbose_name='名称')
    user = models.ForeignKey(UserModel, on_delete=models.DO_NOTHING, db_constraint=False, verbose_name='用户')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name_plural = verbose_name = 'Feeling'
        db_table = 'user_feeling'

    def __str__(self):
        return self.emoji


class Moment(Writing):
    """
        1. feel字段表示心情, 用emoji表示
    """
    content = models.CharField(max_length=2000, verbose_name='内容')
    occurred_time = models.DateTimeField(default=timezone.now, verbose_name='发生时间', db_index=True)
    feeling = models.ForeignKey(Feeling, on_delete=models.DO_NOTHING, db_constraint=False, verbose_name='心情',
                                null=True, blank=True)

    class Meta:
        verbose_name_plural = verbose_name = '动态'
        ordering = ('-occurred_time', )
        db_table = 'user_moment'

    def head(self):
        return self.content[:20]
    head.__name__ = '内容'

    def __str__(self):
        return self.head()
