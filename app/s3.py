import boto
from flask import current_app
from boto.s3.key import Key
from .logger import log
import boto.s3.connection


def upload_to_s3(file, filename, url_expires_in=0, url_query_auth=False, url_force_http=False):
    boto.set_stream_logger('boto')
    conn = boto.connect_s3(current_app.config['AWS_ACCESS_KEY'], current_app.config['AWS_SECRET_KEY'])
    bucket = conn.get_bucket(current_app.config['AWS_BUCKET_NAME'])

    k = Key(bucket)
    k.key = filename
    k.set_metadata('Content-Type', 'image/jpeg')
    k.set_contents_from_string(file)
    # k.set_acl('public-read')
    k.make_public()
    log.info('uploaded file %s to bucket %s' % (filename, bucket))
    return k.generate_url(url_expires_in, query_auth=url_query_auth, force_http=url_force_http)

