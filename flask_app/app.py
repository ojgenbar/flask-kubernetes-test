import os
import socket

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


@app.route('/db-info/', methods=['POST'])
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
