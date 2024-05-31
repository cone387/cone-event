from django.db.models import TextChoices


class OauthPlatform(TextChoices):
    DINGDING = 'DINGDING', '钉钉'
