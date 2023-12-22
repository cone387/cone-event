from django.contrib import admin
from django.db.models import Count
from django.utils.html import format_html
from . import models
from . import forms
from .choices import MediaEngine


class UserAdmin(admin.ModelAdmin):

    def save_form(self, request, form, change):
        if not change:
            form.instance.user = request.user
        return super().save_form(request, form, change)


class MediaAdmin(UserAdmin):
    form = forms.MediaForm
    list_display = ('id', 'model', 'type', 'name', 'size', 'engine', 'upload_time')
    fields = (
        "engine",
        ("model", "type", ),
        ("uri", "size"),
        "media_url",
        ("extra", ),
        ("upload_time", "create_time", "user"),
    )
    readonly_fields = ('size', 'create_time', 'upload_time', 'user')
    list_filter = ('model', 'type', 'engine')

    def name(self, obj: models.Media):
        if obj.engine == MediaEngine.QINIU:
            try:
                url = obj.uri.url
            except ValueError:
                url = ''
            return format_html(
                '<a href="{}" target="_blank">{}</a>',
                url,
                obj.uri.name
            ) if url else ''
        return format_html(
            '<img src="{}" style="max-width: 80px; max-height: 80px;"/>',
            obj.uri.url
        )
    name.__name__ = '文件'

    def save_form(self, request, form, change):
        form.instance.size = form.instance.uri.size
        return super().save_form(request, form, change)

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            obj: models.Media
            obj.uri.storage.delete(obj.uri.name)
        return super(MediaAdmin, self).delete_queryset(request, queryset)


class TagAdmin(UserAdmin):
    form = forms.TagForm
    list_display = ('id', 'label', 'create_time', 'user')
    fields = ("name", "color")

    def label(self, obj):
        return format_html('<span style="color: {}">{}</span>', obj.color, obj.name)
    label.__name__ = '标签'


class FeelingAdmin(UserAdmin):
    list_display = ('id', 'emoji', 'name', 'create_time', 'user')
    fields = ("emoji", "name")
    readonly_fields = ('user', 'create_time')


class FeelingChoiceFilter(admin.SimpleListFilter):
    title = '心情'
    parameter_name = 'feeling'

    def lookups(self, request, model_admin):
        queryset = models.Moment.objects.filter(user=request.user).values_list('feeling__emoji').annotate(
            count=Count('id')
        ).filter(count__gt=0).values_list('feeling_id', 'feeling__emoji')
        none = False
        for x in queryset:
            if x[1] is None:
                if not none:
                    none = True
                    yield -1, '空'
            else:
                yield x

    def queryset(self, request, queryset):
        if self.value():
            if self.value() == '-1':
                return queryset.filter(feeling__isnull=True)
            return queryset.filter(feeling_id=self.value())
        return queryset


class MomentAdmin(UserAdmin):
    form = forms.MomentForm
    list_display = ('id', 'feeling', 'head', 'tag', 'admin_media', 'occurred_time', 'writing_status', 'user')
    filter_horizontal = ('medias', 'tags')
    fieldsets = (
        (None, {
            'fields': ('feeling', 'content', 'occurred_time', 'medias', 'tags')
        }),
        ("高级", {
            'classes': ('collapse',),
            'fields': ('extra', )
        })
    )
    list_filter = (FeelingChoiceFilter, 'tags', 'writing_status')
    search_fields = ("content", )

    def tag(self, obj):
        return ','.join([x.name for x in obj.tags.all()])
    tag.__name__ = '标签'

    def admin_media(self, obj: models.Moment):
        c = obj.medias.all().count()
        return '%s媒体' % c if c else ''
    admin_media.__name__ = '媒体'

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name in ('tags', 'medias'):
            kwargs["queryset"] = models.Media.objects.filter(user=request.user)
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def get_queryset(self, request):
        return super().get_queryset(request).filter(
            # writing_status=models.WritingStatus.OK
        ).select_related('feeling').prefetch_related('tags', 'medias')


admin.site.site_header = 'Writing Manage'
admin.site.site_title = 'Writing Manage'

admin.site.register(models.Tag, TagAdmin)
admin.site.register(models.Media, MediaAdmin)
admin.site.register(models.Feeling, FeelingAdmin)
admin.site.register(models.Moment, MomentAdmin)
