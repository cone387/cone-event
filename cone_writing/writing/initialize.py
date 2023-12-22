import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cone_writing.settings')
django.setup()
from writing.models import Tag, Feeling, get_user_model


default_tags = [
    {'name': '工作', 'color': '#FF0000'},
    {'name': '学习', 'color': '#FF7F00'},
    {'name': '生活', 'color': '#FFFF00'},
    {'name': '娱乐', 'color': '#00FF00'},
    {'name': '运动', 'color': '#00FFFF'},
    {'name': '休息', 'color': '#0000FF'},
    {'name': '睡觉', 'color': '#8B00FF'},
    {'name': '其他', 'color': '#000000'},
    {'name': 'Python', 'color': '#FF0000'},
    {'name': 'Django', 'color': '#FF7F00'},
]


default_feelings = [
    {'emoji': '😀', 'name': '开心'},
    {'emoji': '😂', 'name': '大笑'},
    {'emoji': '😍', 'name': '喜欢'},
    {'emoji': '😎', 'name': '酷'},
    {'emoji': '😭', 'name': '哭'},
    {'emoji': '😡', 'name': '生气'},
    {'emoji': '😱', 'name': '惊讶'},
    {'emoji': '😴', 'name': '困'},
    {'emoji': '😷', 'name': '生病'},
    {'emoji': '😈', 'name': '坏笑'},
    {'emoji': '😳', 'name': '害羞'},
    {'emoji': '😜', 'name': '调皮'},
    {'emoji': '😇', 'name': '天使'},
    {'emoji': '😘', 'name': '亲亲'},
    {'emoji': '😋', 'name': '美味'},
    {'emoji': '😒', 'name': '不开心'},
    {'emoji': '😑', 'name': '无语'},
    {'emoji': '😢', 'name': '伤心'},
    {'emoji': '😤', 'name': '气'},
    {'emoji': '😰', 'name': '紧张'},
    {'emoji': '😩', 'name': '疲惫'},
    {'emoji': '😵', 'name': '晕'},
    {'emoji': '😲', 'name': '惊讶'},
    {'emoji': '😞', 'name': '失望'},
    {'emoji': '😟', 'name': '担心'},
    {'emoji': '😕', 'name': '疑惑'},
    {'emoji': '😮', 'name': '惊讶'},
    {'emoji': '😣', 'name': '痛苦'},
    {'emoji': '😧', 'name': '焦虑'},
    {'emoji': '😦', 'name': '震惊'},
    {'emoji': '😈', 'name': '坏笑'},
    {'emoji': '😬', 'name': '尴尬'},
    {'emoji': '😶', 'name': '沉默'},
    {'emoji': '😐', 'name': '无奈'},
    {'emoji': '😯', 'name': '惊讶'},
]


def create_tags(user):
    for i, item in enumerate(default_tags):
        tag, created = Tag.objects.get_or_create(user=user, **item)
        if created:
            print('%s. create tag %s' % (i, tag))


def create_feelings(user):
    for i, item in enumerate(default_feelings):
        feeling, created = Feeling.objects.get_or_create(user=user, **item)
        if created:
            print('%s. create feeling %s' % (i, feeling))


if __name__ == '__main__':
    user = get_user_model().objects.filter(is_superuser=True).first()
    create_feelings(user)
    create_tags(user)
