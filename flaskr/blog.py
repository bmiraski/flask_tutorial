from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db

import sqlite3

bp = Blueprint('blog', __name__)


def get_post(id, check_author=True):
    post = get_db().execute(
        'SELECT p.id, title, body, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' WHERE p.id = ?',
        (id,)
    ).fetchone()

    if post is None:
        abort(404, f"Post id {id} doesn't exist.")

    if check_author and post['author_id'] != g.user['id']:
        abort(403)

    return post


@bp.route('/')
def index():
    db = get_db()
    posts = db.execute(
        'SELECT p.id, title, body, created, likes, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' ORDER BY created DESC'
    ).fetchall()
    post_likes = {}

    db.row_factory = sqlite3.Row

    cur = db.cursor()
    cur.execute(
        'SELECT p.id, title, body, created, likes, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' ORDER BY created DESC')

    rows = cur.fetchall()

    for row in rows:
        p_likes = db.execute(
            'SELECT COUNT(id) from likes where post_id = ? ', (row['id'],)
            ).fetchone()
        post_likes[row['id']] = tuple(p_likes)[0]

    return render_template('blog/index.html', posts=posts, plikes=post_likes)


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO post (title, body, author_id)'
                ' VALUES (?, ?, ?)',
                (title, body, g.user['id'])
            )
            db.commit()
            return redirect(url_for('blog.index'))

    return render_template('blog/create.html')


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    post = get_post(id)

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE post SET title = ?, body = ?'
                ' WHERE id = ?',
                (title, body, id)
            )
            db.commit()
            return redirect(url_for('blog.index'))

    return render_template('blog/update.html', post=post)


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_post(id)
    db = get_db()
    db.execute('DELETE FROM post WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('blog.index'))


@bp.route('/<int:id>/display')
def display(id):
    db = get_db()
    post = db.execute('SELECT * from post where id = ?', (id,)).fetchone()
    likes = db.execute('SELECT COUNT(id) from likes where post_id = ?',
                       (id,)).fetchone()
    like_list = list(db.execute('SELECT user_id from likes where post_id = ?',
                     (id,)).fetchall())

    ll = [like[0] for like in like_list]
    return render_template('blog/display.html', post=post, likes=likes,
                           like_list=ll)


@bp.route('/<int:id>/<int:user_id>/like')
def like(id, user_id):
    db = get_db()
    db.execute('INSERT INTO likes (post_id, user_id) VALUES (?, ?)',
               (id, user_id))
    db.commit()
    return redirect(url_for('blog.display', id=id))


@bp.route('/<int:id>/<int:user_id>/unlike')
def unlike(id, user_id):
    db = get_db()
    db.execute('DELETE from likes WHERE post_id = ? AND user_id = ?',
               (id, user_id))
    db.commit()
    return redirect(url_for('blog.display', id=id))
