import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cone_writing.settings')
django.setup()

from django.conf import settings
from qiniu import Auth, put_file, etag


QINIU_ACCESS_KEY = getattr(settings, 'QINIU_ACCESS_KEY')
QINIU_SECRET_KEY = getattr(settings, 'QINIU_SECRET_KEY')
QINIU_BUCKET_NAME = getattr(settings, 'QINIU_BUCKET_NAME')
QINIU_BUCKET_DOMAIN = getattr(settings, 'QINIU_BUCKET_DOMAIN')
QINIU_SECURE_URL = getattr(settings, 'QINIU_SECURE_URL', False)


auth = Auth(QINIU_ACCESS_KEY, QINIU_SECRET_KEY)

# 上传文件到存储后， 存储服务将文件名和文件大小回调给业务服务器。
policy = {
    'callbackUrl': 'http://your.domain.com/callback.php',
    'callbackBody': 'filename=$(fname)&filesize=$(fsize)'
}


def gen_token(key=None, bucket=QINIU_BUCKET_NAME):
    return auth.upload_token(bucket, None, 3600)


def gen_key_and_token(filename, scope=None, user_id=None, bucket=QINIU_BUCKET_NAME):
    key = 'writing/%s/%s/%s' % ((scope or 'default').strip('/').lower(), user_id, filename.strip('/'))
    token = auth.upload_token(bucket, key, 3600)
    return key, token


def upload_file(file, key, token):
    ret, info = put_file(token, key, file, version='v2')
    assert ret['key'] == key
    assert ret['hash'] == etag(file)


if __name__ == '__main__':
    print(gen_key_and_token('test.jpg'))
