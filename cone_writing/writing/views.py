from django.db.models import Count
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import NotFound, ParseError, ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet, ModelViewSet
from rest_framework.mixins import CreateModelMixin, ListModelMixin, DestroyModelMixin, UpdateModelMixin
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from drf_multiple_model.views import ObjectMultipleModelAPIView
from drf_multiple_model.pagination import MultipleModelLimitOffsetPagination
from django.db.models import Q
from django.db import connection
from .models import upload_to
from .choices import WritingStatus
from . import serializers
from . import filters
from . import pagination
from . import models
from utils import qiniu_cloud


# 七牛文件视图
class QiNiuStorageView:

    @staticmethod
    @api_view(http_method_names=['GET'])
    @permission_classes([IsAuthenticated, ])
    def get_upload_token(request: Request):
        """
        获取上传token
        :param request:
            request.query_params: {
                'model': 'moment',
                'filename': 'xxx.jpg'
            }
        :return: Response
        """
        filename = request.query_params.get('filename')
        if not filename:
            return Response(data={'error': 'filename is required'}, status=status.HTTP_400_BAD_REQUEST)
        model = request.query_params.get('model')
        media = models.Media(model=model, user=request.user)
        key = upload_to(media, filename)
        token = qiniu_cloud.gen_token(upload_to(media, filename))
        return Response(data={'key': key, 'token': token})


class MediaViewSet(CreateModelMixin, DestroyModelMixin, GenericViewSet):
    serializer_class = serializers.MediaSerializer
    queryset = models.Media.objects.all()


class WritingViewMixin:
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    # def perform_destroy(self, instance: Writing):
    #     if self.request.query_params.get('delete') == '1':
    #         # delete=1时强制删除
    #         instance.delete()
    #     else:
    #         instance.writing_status = WritingStatus.DELETED
    #         instance.save()


class MultiDestroyModelMixin:
    lookup_field = 'pk'

    def get_objects(self):
        object_string = self.request.query_params.get('object', '').split(',')
        if not object_string:
            raise ValidationError({"error": "object param is required"})
        object_ids = []
        for obj in object_string:
            obj = obj.strip()
            if obj.isdigit():
                object_ids.append(obj)
            else:
                raise ValidationError({"error": "object id must be digit"})
        objects = self.get_queryset().filter(pk__in=object_ids).values_list('id', flat=True)
        if len(objects) != len(object_ids):
            not_found = [obj for obj in object_ids if obj not in objects]
            raise NotFound({"error": "对象 %s not found" % not_found})
        return objects

    def destroy(self, request, *args, **kwargs):
        objects = self.get_objects()
        self.perform_destroy(objects)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_destroy(self, objects):
        with connection.cursor() as cursor:
            if len(objects) == 1:
                delete = "id = %s" % objects[0]
            else:
                delete = f"id IN {tuple(objects)}"
            command = "UPDATE %s SET writing_status = %s WHERE %s" % (
                self.queryset.model._meta.db_table, WritingStatus.DELETED, delete
            )
            cursor.execute(command)


class TagViewSet(WritingViewMixin, CreateModelMixin, ListModelMixin, DestroyModelMixin, GenericViewSet):
    """
        can: create, list, destroy
    """
    queryset = models.Tag.objects.all()
    serializer_class = serializers.TagSerializer
    permission_classes = (IsAuthenticated, )
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('name',)
    pagination_class = None

    def perform_create(self, serializer):
        try:
            serializer.save(user=self.request.user)
        except models.Tag.DoesNotExist:
            raise NotFound()


class FeelingViewSet(ModelViewSet):
    serializer_class = serializers.FeelingSerializer
    queryset = models.Feeling.objects.all()


class MomentViewSet(WritingViewMixin, CreateModelMixin, ListModelMixin, MultiDestroyModelMixin, GenericViewSet):
    """
        option: create, list, destroy
    """
    serializer_class = serializers.MomentSerializer
    queryset = models.Moment.objects.filter(~Q(writing_status=WritingStatus.DELETED)
                                            ).select_related('feeling').prefetch_related('tags')
    pagination_class = pagination.MomentPagination
    filterset_class = filters.MomentFilter

    @staticmethod
    @api_view(http_method_names=['GET'])
    @permission_classes([IsAuthenticated, ])
    def group(request: Request):
        """
        :param request:
        :by: group by occurred_time_date, week, month, year
        :return:
        """
        by: str = request.query_params.get('by', '')
        bys = by.split(',')
        if not (x in ['month', 'feeling', 'tag'] for x in bys):
            data = {"error": "not support, only support month and feeling now"}
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)
        if not by:
            bys = ['month', 'feeling', 'tag']
        groups = {}
        queryset = MomentViewSet.queryset.filter(user=request.user)
        for by in bys:
            if by == 'month':
                data = queryset.extra(
                    select={'month': "DATE_FORMAT('occurred_time', '%%Y-%%m')"}  # for mysql
                    # select={'month': "strftime('%%Y-%%m', occurred_time)"}     # for sqlite
                ).values('month').annotate(count=Count('id')).values('month', 'count').order_by('-month')
            elif by == 'feeling':
                with connection.cursor() as cursor:
                    command = """
                        SELECT f.id, f.emoji, f.name, IFNULL(m.count, 0) FROM user_feeling f LEFT JOIN (
                            SELECT feeling_id, user_id, count(*) AS count FROM user_moment 
                            WHERE user_id = {user_id} AND writing_status = {writing_status} GROUP BY feeling_id
                        ) m on f.id = m.feeling_id AND m.user_id = f.user_id 
                        UNION 
                            SELECT 0, '', '无', count(id) FROM user_moment 
                            WHERE user_moment.user_id = {user_id} 
                            AND writing_status = {writing_status} AND feeling_id IS NULL 
                        """.format(writing_status=WritingStatus.OK, user_id=request.user.id)
                    cursor.execute(command)
                    data = cursor.fetchall()
                    data = [{'id': pk, 'emoji': emoji, 'name': name, 'count': count} for pk, emoji, name, count in data]
            else:
                data = queryset.values(
                    "tags__name"
                ).annotate(count=Count('id')).values("tags__name", "tags__color", 'count')
            groups[by] = data
        return Response(groups)


class ThingViewSet(CreateModelMixin, ListModelMixin, MultiDestroyModelMixin, GenericViewSet):
    serializer_class = serializers.ThingSerializer
    queryset = models.Thing.objects.all().select_related('parent', 'feeling')
    # pagination_class = pagination.ThingPagination
    filterset_class = filters.ThingFilter


class FeelingRecordView(ModelViewSet):
    serializer_class = serializers.FeelingRecordSerializer
    queryset = models.FeelingRecord.objects.all().select_related('feeling')
    pagination_class = pagination.DefaultPagination
    filterset_class = filters.FeelingRecordFilter


class SearchView(ObjectMultipleModelAPIView):
    permission_classes = (IsAuthenticated,)
    pagination_class = MultipleModelLimitOffsetPagination

    querylist = [
        {
            'queryset': models.Moment.objects.filter(~Q(writing_status=WritingStatus.DELETED)),
            'serializer_class': serializers.MomentSerializer,
            'filter_fn': filters.filter_moment,
            'label': 'moment'
        },
    ]

    def get(self, request: Request, *args, **kwargs):
        if not request.query_params.get('q'):
            return Response(data={'error': 'param q is required'}, status=400)
        return super(SearchView, self).get(request, *args, **kwargs)

    def load_queryset(self, query_data, request, *args, **kwargs):
        query_data['queryset'] = query_data['queryset'].filter(user=request.user)
        return super().load_queryset(query_data, request, *args, **kwargs)
