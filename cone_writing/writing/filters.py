from django_filters import rest_framework as filters
from . import models


def filter_moment(queryset, request):
    q = request.query_params.get('q')
    return queryset.filter(content__contains=q)


class MomentFilter(filters.FilterSet):
    tag = filters.CharFilter(field_name='tags__name', lookup_expr='exact')
    date = filters.DateFilter(field_name='occurred_time', lookup_expr='date')
    month = filters.CharFilter(field_name='occurred_time', method='filter_month')

    @staticmethod
    def filter_month(queryset, name, value):
        year, month = value.split('-')
        return queryset.filter(occurred_time__year=year, occurred_time__month=month)

    class Meta:
        model = models.Moment
        fields = {
            "content": ["contains"],
            "feeling__emoji": ["exact"],
            "feeling__name": ["exact"],
            "occurred_time": ["gte", "lte"],
            "create_time": ["gte", "lte"],
        }


class ThingFilter(filters.FilterSet):
    has_feeling = filters.BooleanFilter(field_name='feeling_id', lookup_expr='isnull', exclude=True)

    class Meta:
        model = models.Thing
        fields = {
            "name": ["contains"],
            "feeling__emoji": ["exact"],
            "feeling__name": ["exact"],
            "create_time": ["gte", "lte"],
        }


class FeelingRecordFilter(filters.FilterSet):
    class Meta:
        model = models.FeelingRecord
        fields = {
            "feeling__emoji": ["exact"],
            "feeling__name": ["exact"],
            "create_time": ["gte", "lte"],
        }
