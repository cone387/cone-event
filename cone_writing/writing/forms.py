# -*- coding:utf-8 -*-

# author: Cone
# datetime: 2021-03-15 10:53
# software: PyCharm
from django import forms
from django.core.validators import URLValidator
from . import validators
from .choices import MediaType
from .storage import QiniuStorage


class MediaForm(forms.ModelForm):
    media_url = forms.CharField(required=False, label='媒体地址', widget=forms.TextInput(
        attrs={'width': '80%', 'placeholder': '自定义媒体地址'}
    ))
    uri = forms.FileField(required=False, label='媒体文件')

    def clean(self):
        cleaned_data = super(MediaForm, self).clean()
        if not self.errors:
            if not cleaned_data['media_url'] and not cleaned_data['uri']:
                raise forms.ValidationError('媒体地址和媒体文件至少填写一个')
            if cleaned_data['media_url'] and cleaned_data['uri']:
                raise forms.ValidationError('媒体地址和媒体文件只能填写一个')
            if cleaned_data['media_url']:
                # 检验url是否合法
                URLValidator()(cleaned_data['media_url'])
                cleaned_data['uri'] = QiniuStorage().fetch(cleaned_data['media_url'])
            if cleaned_data['type'] == MediaType.AUTO:
                cleaned_data['type'] = MediaType.detect(cleaned_data['uri'].name)
        return cleaned_data


class MomentForm(forms.ModelForm):
    content = forms.CharField(widget=forms.Textarea(attrs={'rows': 5, 'cols': 100}), label='内容')


class TagForm(forms.ModelForm):

    def clean(self):
        cleaned_data = super(TagForm, self).clean()
        if not self.errors and cleaned_data['color']:
            validators.color_validator(cleaned_data['color'])
        return cleaned_data
