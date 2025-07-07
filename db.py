import psycopg2
import time
from flask import session

database = psycopg2.connect('postgres://avnadmin:AVNS_2ueBhbBr1ThcNLin5sg@blog00-blog00543-3325.e.aivencloud.com:22320/defaultdb?sslmode=require')
cursor = database.cursor()


def insert_user(name, username, email, password, gender, role, created):
    query = ''' insert into Users(name, username, email, password, gender, role, created_at)
            values('{}', '{}', '{}', '{}', '{}', '{}', {})
            '''.format(name, username, email, password, gender, role, created)
    cursor.execute(query)
    database.commit()


def check_if_user_exists(email, username):
    cursor.execute(f''' select 1 from Users where email='{email}' ''')
    database.commit()
    if cursor.fetchone():
        return 'Email already registered'
    cursor.execute(f''' select 1 from Users where username='{username}' ''')
    database.commit()
    if cursor.fetchone():
        return 'Username already taken'
    return False


def login(username, password):
    query = ''' select name, username, email, role from Users where (email='{}' or username='{}') and password='{}'
            '''.format(username, username, password)
    cursor.execute(query)
    database.commit()
    return cursor.fetchone()


def get_categories():
    cursor.execute(''' select * from categories ''')
    categories = cursor.fetchall()
    categories = [i[0] for i in categories]
    database.commit()
    return categories


def table_last_id():
    query = '''  select max(id) from Posts '''
    cursor.execute(query)
    database.commit()
    ID = cursor.fetchone()
    if ID[0]:
        return ID[0]
    else:
        return 0


def insert_post(title, content, image, author_username, category, status):
    query = ''' insert into Posts(title, content, image_filename, author_username, category, status, created_at, updated_at)
            values('{}', '{}', '{}', '{}', '{}', '{}', {}, {})
            '''.format(title, content, image, author_username, category, status, time.time(), time.time())
    cursor.execute(query)
    database.commit()


def get_approved_posts(dct):
    query = ''' select * from posts where status='Approved' '''
    if 'category' in dct:
        query += f''' and category='{dct['category']}' '''
    if 'search' in dct:
        query += f''' and title like '%{dct['search']}%' '''
    if 'sort' in dct:
        if dct['sort'] == 'time_asc':
            query += f''' Order By created_at asc '''
        else:
            query += f''' Order By created_at desc '''
    cursor.execute(query)
    database.commit()
    return cursor.fetchall()


def get_posts():
    cursor.execute(''' select * from posts ''')
    database.commit()
    return cursor.fetchall()


def get_post_data(post_id):
    cursor.execute(''' select * from Posts where id='{}' '''.format(post_id))
    database.commit()
    return cursor.fetchone()


def add_visit_to_post(post_id):
    cursor.execute(''' update Posts set visits=visits+1 where ID={} '''.format(post_id))
    database.commit()


def add_comment_to_post(post_id, username, comment_text, created):
    query = ''' insert into Comments(post_id, username, comment_text, created_at)
            values({}, '{}', '{}', {});
            '''.format(post_id, username, comment_text, created)
    cursor.execute(query)
    database.commit()

    cursor.execute(''' update Posts set comments=comments+1 where ID={} '''.format(post_id))
    database.commit()


def get_comments_of_post(post_id):
    cursor.execute(''' select * from Comments where post_id={} '''.format(post_id))
    database.commit()
    return cursor.fetchall()


def delete_comment(post_id, comment_id):
    cursor.execute(f''' select username from Comments where ID={comment_id} ''')
    database.commit()
    if cursor.fetchone()[0] == session['username']:
        cursor.execute(''' delete from Comments where ID={} '''.format(comment_id))
        database.commit()

        cursor.execute(''' update Posts set comments=comments-1 where ID={} '''.format(post_id))
        database.commit()


###################### admin ##########################
def post_action(post_id, action):
    cursor.execute(''' update posts set status='{}' where ID={} '''.format(action, post_id))
    database.commit()


def admin_delete_post(post_id):
    cursor.execute(f''' delete from posts where id={post_id} ''')
    database.commit()


def get_all_users():
    cursor.execute(''' select * from users ''')
    database.commit()
    return cursor.fetchall()


def get_logged_in_user():
    cursor.execute(f''' select name, username, email, gender from Users where username='{session['username']}' ''')
    database.commit()
    return cursor.fetchone()


def get_logged_in_user_posts():
    cursor.execute(f''' select * from Posts where author_username='{session['username']}' ''')
    database.commit()
    return cursor.fetchall()


def update_profile(name, email, username, gender):
    cursor.execute(f''' update Users set name='{name}', email='{email}', username='{username}', gender='{gender}' where username='{session['username']}' ''')
    database.commit()


def check_if_user_exists_while_update(email, username):
    cursor.execute(f''' select 1 from Users where email='{email}' and email !='{session['email']}' ''')
    database.commit()
    data = cursor.fetchone()
    if data:
        return 'Email already registered'
    cursor.execute(f''' select 1 from Users where username='{username}' and username !='{session['username']}' ''')
    database.commit()
    if cursor.fetchone():
        return 'Username already taken'
    return False


def delete_own_post(post_id):
    cursor.execute(f''' delete from posts where ID={post_id} and author_username='{session['username']}' ''')
    database.commit()


def get_post_image_filename(post_id):
    cursor.execute(f''' select image_filename from posts where id={post_id} ''')
    database.commit()
    return cursor.fetchone()[0]


def edit_post(post_id, title, category, content):
    cursor.execute(f''' update posts set title='{title}', category='{category}', content='{content}' where id={post_id} ''')
    database.commit()
