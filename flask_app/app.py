import os
import socket
import uuid

from google.cloud import storage
from flask import Flask
from flask import request
from psycopg2 import extras
import psycopg2.pool


app = Flask(__name__)
application = app

postgreSQL_pool = psycopg2.pool.SimpleConnectionPool(
    minconn=1,
    maxconn=20,
    user=os.getenv('POSTGRES_USER'),
    password=os.getenv('POSTGRES_PASSWORD'),
    host=os.getenv('POSTGRES_HOST'),
    port=os.getenv('POSTGRES_PORT'),
    database=os.getenv('POSTGRES_DATABASE'),
)

CLOUD_STORAGE_BUCKET = os.getenv('CLOUD_STORAGE_BUCKET')

hostname = socket.gethostname()


def fetch_query(query, args):
    connection = postgreSQL_pool.getconn()
    cursor = connection.cursor()
    cursor.execute(query, args)
    result = cursor.fetchall()
    cursor.close()
    connection.commit()
    postgreSQL_pool.putconn(connection)
    return result


def response_from_row(row):
    data = {
        'id': row[0],
        'payload': row[1],
        'comment': row[2],
    }
    return data


@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"


@app.route("/hostinfo")
def hostinfo():
    data = {
        "request.remote_addr": request.remote_addr,
        "request.host": request.host,
        "request.host_url": request.host_url,
        'system.hostname': hostname,
    }
    return data


@app.route('/db-info', methods=['POST'])
def db_info():
    data = request.json
    payload = extras.Json(data['payload'])
    comment = data.get('comment')
    query = 'INSERT INTO info (data, comment) VALUES (%s, %s) RETURNING id'
    id_ = fetch_query(query, [payload, comment])[0][0]
    return {'id': id_}


@app.route('/db-info/<row_id>', methods=['GET', 'DELETE'])
def db_info_id(row_id):
    row_id = int(row_id)
    if request.method == 'DELETE':
        query = 'DELETE FROM info WHERE id = %s RETURNING id, data, comment;'
        rows = fetch_query(query, [row_id])
        if not rows:
            response = {
                'status': 'NOT_FOUND',
                'message': f'Row with ID = {row_id} not found.'
            }
        else:
            response = response_from_row(rows[0])
    else:
        query = 'SELECT * FROM info WHERE id = %s;'
        rows = fetch_query(query, [row_id])
        if not rows:
            response = {
                'status': 'NOT_FOUND',
                'message': f'Row with ID = {row_id} not found.'
            }
        else:
            response = response_from_row(rows[0])
    return response


@app.route('/image')
def image_index() -> str:
    return """
<form method="POST" action="image/upload" enctype="multipart/form-data">
    <input type="file" name="file">
    <input type="submit">
</form>
"""


@app.route('/image/upload', methods=['POST'])
def image_upload() -> dict:
    uploaded_file = request.files.get('file')

    if not uploaded_file:
        return {
            'status': 'NO_FILE',
            'message': 'No file provided'
        }

    gcs = storage.Client()
    bucket = gcs.get_bucket(CLOUD_STORAGE_BUCKET)

    blob = bucket.blob(uuid.uuid4().hex + uploaded_file.filename)
    blob.upload_from_string(
        uploaded_file.read(),
        content_type=uploaded_file.content_type
    )
    blob.make_public()
    return {'public_url': blob.public_url}
