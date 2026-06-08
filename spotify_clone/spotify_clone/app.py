from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3, os, uuid
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = 'spotify_clone_secret_key_2024'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
MUSIC_FOLDER = os.path.join(UPLOAD_FOLDER, 'music')
COVER_FOLDER = os.path.join(UPLOAD_FOLDER, 'covers')
AVATAR_FOLDER = os.path.join(UPLOAD_FOLDER, 'avatars')

ALLOWED_AUDIO = {'mp3', 'wav', 'ogg', 'm4a', 'flac'}
ALLOWED_IMAGE = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'admin123'

def get_db():
    db = sqlite3.connect(os.path.join(BASE_DIR, 'spotify.db'))
    db.row_factory = sqlite3.Row
    return db

def init_db():
    db = get_db()
    c = db.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        avatar TEXT DEFAULT 'default.png',
        is_banned INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        last_login TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS genres (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        color TEXT DEFAULT '#1DB954',
        icon TEXT DEFAULT '🎵'
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS albums (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        artist TEXT NOT NULL,
        genre_id INTEGER,
        cover TEXT DEFAULT 'default_cover.jpg',
        description TEXT,
        release_year INTEGER,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(genre_id) REFERENCES genres(id)
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS songs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        artist TEXT NOT NULL,
        album_id INTEGER,
        genre_id INTEGER,
        duration INTEGER DEFAULT 0,
        file_path TEXT NOT NULL,
        cover TEXT DEFAULT 'default_cover.jpg',
        plays INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(album_id) REFERENCES albums(id),
        FOREIGN KEY(genre_id) REFERENCES genres(id)
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS playlists (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        cover TEXT DEFAULT 'default_cover.jpg',
        description TEXT,
        is_public INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS playlist_songs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        playlist_id INTEGER NOT NULL,
        song_id INTEGER NOT NULL,
        added_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(playlist_id) REFERENCES playlists(id),
        FOREIGN KEY(song_id) REFERENCES songs(id)
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS saved_songs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        song_id INTEGER NOT NULL,
        saved_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(song_id) REFERENCES songs(id),
        UNIQUE(user_id, song_id)
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS login_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        username TEXT,
        action TEXT,
        ip_address TEXT,
        timestamp TEXT DEFAULT CURRENT_TIMESTAMP
    )''')

    # Seed genres
    genres = [
        ('Pop', '#FF6B6B', '🎤'), ('Rock', '#FF8E53', '🎸'), ('Hip-Hop', '#FFA07A', '🎧'),
        ('Jazz', '#4ECDC4', '🎷'), ('Classical', '#45B7D1', '🎻'), ('Electronic', '#96CEB4', '🎹'),
        ('R&B', '#DDA0DD', '💜'), ('Country', '#F4A460', '🤠'), ('Reggae', '#98D8C8', '🌴'),
        ('Metal', '#708090', '🤘'), ('Blues', '#6495ED', '🎺'), ('Latin', '#FF69B4', '💃'),
        ('Indie', '#20B2AA', '🌟'), ('Folk', '#D2691E', '🪕'), ('Soul', '#FF7F50', '❤️')
    ]
    for g in genres:
        c.execute('INSERT OR IGNORE INTO genres(name,color,icon) VALUES(?,?,?)', g)

    db.commit()
    db.close()

def login_required(f):
    @wraps(f)
    def dec(*args, **kwargs):
        if 'user_id' not in session and not session.get('is_admin'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return dec

def admin_required(f):
    @wraps(f)
    def dec(*args, **kwargs):
        if not session.get('is_admin'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return dec

def allowed_audio(fn): return '.' in fn and fn.rsplit('.',1)[1].lower() in ALLOWED_AUDIO
def allowed_image(fn): return '.' in fn and fn.rsplit('.',1)[1].lower() in ALLOWED_IMAGE

def save_file(file, folder):
    ext = file.filename.rsplit('.',1)[1].lower()
    fn = str(uuid.uuid4()) + '.' + ext
    file.save(os.path.join(folder, fn))
    return fn

# ─── AUTH ───────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    if session.get('is_admin'):
        return redirect(url_for('admin_dashboard'))
    if 'user_id' in session:
        return redirect(url_for('home'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        ip = request.remote_addr

        # Admin check
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session.clear()
            session['is_admin'] = True
            session['admin_name'] = 'Admin'
            db = get_db()
            db.execute('INSERT INTO login_logs(username,action,ip_address) VALUES(?,?,?)',
                       ('admin','admin_login',ip))
            db.commit(); db.close()
            return redirect(url_for('admin_dashboard'))

        db = get_db()
        user = db.execute('SELECT * FROM users WHERE username=?',(username,)).fetchone()
        if user and check_password_hash(user['password'], password):
            if user['is_banned']:
                db.close()
                flash('Your account has been banned. Contact support.','error')
                return render_template('login.html')
            session.clear()
            session['user_id'] = user['id']
            session['username'] = user['username']
            db.execute('UPDATE users SET last_login=? WHERE id=?',(datetime.now().isoformat(),user['id']))
            db.execute('INSERT INTO login_logs(user_id,username,action,ip_address) VALUES(?,?,?,?)',
                       (user['id'],username,'login',ip))
            db.commit(); db.close()
            return redirect(url_for('home'))
        db.close()
        flash('Invalid credentials','error')
    return render_template('login.html')

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip()
        password = request.form['password']
        db = get_db()
        try:
            db.execute('INSERT INTO users(username,email,password) VALUES(?,?,?)',
                       (username, email, generate_password_hash(password)))
            db.commit()
            flash('Account created! Please login.','success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username or email already exists.','error')
        finally:
            db.close()
    return render_template('register.html')

@app.route('/logout')
def logout():
    if 'user_id' in session:
        db = get_db()
        db.execute('INSERT INTO login_logs(user_id,username,action,ip_address) VALUES(?,?,?,?)',
                   (session['user_id'],session.get('username'),'logout',request.remote_addr))
        db.commit(); db.close()
    session.clear()
    return redirect(url_for('login'))

# ─── USER PAGES ─────────────────────────────────────────────────────────────

@app.route('/home')
@login_required
def home():
    db = get_db()
    genres = db.execute('SELECT * FROM genres').fetchall()
    featured = db.execute('''SELECT s.*,g.name as genre_name,g.color FROM songs s
        LEFT JOIN genres g ON s.genre_id=g.id ORDER BY s.plays DESC LIMIT 12''').fetchall()
    recent = db.execute('''SELECT s.*,g.name as genre_name FROM songs s
        LEFT JOIN genres g ON s.genre_id=g.id ORDER BY s.created_at DESC LIMIT 12''').fetchall()
    albums = db.execute('SELECT a.*,g.name as genre_name FROM albums a LEFT JOIN genres g ON a.genre_id=g.id ORDER BY a.created_at DESC LIMIT 8').fetchall()
    db.close()
    return render_template('home.html', genres=genres, featured=featured, recent=recent, albums=albums)

@app.route('/genre/<int:genre_id>')
@login_required
def genre(genre_id):
    db = get_db()
    genre = db.execute('SELECT * FROM genres WHERE id=?',(genre_id,)).fetchone()
    songs = db.execute('SELECT * FROM songs WHERE genre_id=? ORDER BY plays DESC',(genre_id,)).fetchall()
    albums = db.execute('SELECT * FROM albums WHERE genre_id=?',(genre_id,)).fetchall()
    db.close()
    return render_template('genre.html', genre=genre, songs=songs, albums=albums)

@app.route('/album/<int:album_id>')
@login_required
def album(album_id):
    db = get_db()
    album = db.execute('SELECT a.*,g.name as genre_name FROM albums a LEFT JOIN genres g ON a.genre_id=g.id WHERE a.id=?',(album_id,)).fetchone()
    songs = db.execute('SELECT * FROM songs WHERE album_id=?',(album_id,)).fetchall()
    db.close()
    return render_template('album.html', album=album, songs=songs)

@app.route('/search')
@login_required
def search():
    q = request.args.get('q','')
    db = get_db()
    songs, albums, genres = [], [], []
    if q:
        like = f'%{q}%'
        songs = db.execute('''SELECT s.*,g.color FROM songs s LEFT JOIN genres g ON s.genre_id=g.id
            WHERE s.title LIKE ? OR s.artist LIKE ?''',(like,like)).fetchall()
        albums = db.execute('SELECT * FROM albums WHERE title LIKE ? OR artist LIKE ?',(like,like)).fetchall()
        genres = db.execute('SELECT * FROM genres WHERE name LIKE ?',(like,)).fetchall()
    db.close()
    return render_template('search.html', q=q, songs=songs, albums=albums, genres=genres)

@app.route('/library')
@login_required
def library():
    db = get_db()
    uid = session['user_id']
    playlists = db.execute('SELECT * FROM playlists WHERE user_id=? ORDER BY created_at DESC',(uid,)).fetchall()
    saved = db.execute('''SELECT s.*,g.name as genre_name,g.color FROM saved_songs ss
        JOIN songs s ON ss.song_id=s.id LEFT JOIN genres g ON s.genre_id=g.id
        WHERE ss.user_id=? ORDER BY ss.saved_at DESC''',(uid,)).fetchall()
    db.close()
    return render_template('library.html', playlists=playlists, saved=saved)

@app.route('/playlist/<int:pid>')
@login_required
def playlist(pid):
    db = get_db()
    pl = db.execute('SELECT p.*,u.username FROM playlists p JOIN users u ON p.user_id=u.id WHERE p.id=?',(pid,)).fetchone()
    if not pl or (pl['user_id'] != session['user_id'] and not pl['is_public']):
        db.close(); return redirect(url_for('library'))
    songs = db.execute('''SELECT s.*,g.name as genre_name,ps.added_at FROM playlist_songs ps
        JOIN songs s ON ps.song_id=s.id LEFT JOIN genres g ON s.genre_id=g.id
        WHERE ps.playlist_id=? ORDER BY ps.added_at''',(pid,)).fetchall()
    db.close()
    return render_template('playlist.html', playlist=pl, songs=songs)

@app.route('/create_playlist', methods=['POST'])
@login_required
def create_playlist():
    name = request.form.get('name','My Playlist')
    desc = request.form.get('description','')
    db = get_db()
    db.execute('INSERT INTO playlists(user_id,name,description) VALUES(?,?,?)',
               (session['user_id'],name,desc))
    db.commit(); db.close()
    flash('Playlist created!','success')
    return redirect(url_for('library'))

@app.route('/delete_playlist/<int:pid>', methods=['POST'])
@login_required
def delete_playlist(pid):
    db = get_db()
    pl = db.execute('SELECT * FROM playlists WHERE id=? AND user_id=?',(pid,session['user_id'])).fetchone()
    if pl:
        db.execute('DELETE FROM playlist_songs WHERE playlist_id=?',(pid,))
        db.execute('DELETE FROM playlists WHERE id=?',(pid,))
        db.commit()
    db.close()
    return redirect(url_for('library'))

# ─── API ENDPOINTS ───────────────────────────────────────────────────────────

@app.route('/api/play/<int:song_id>')
@login_required
def play_song(song_id):
    db = get_db()
    db.execute('UPDATE songs SET plays=plays+1 WHERE id=?',(song_id,))
    db.commit()
    song = db.execute('SELECT * FROM songs WHERE id=?',(song_id,)).fetchone()
    db.close()
    return jsonify({'file': song['file_path'], 'title': song['title'], 'artist': song['artist'], 'cover': song['cover']})

@app.route('/api/save_song/<int:song_id>', methods=['POST'])
@login_required
def save_song(song_id):
    db = get_db()
    existing = db.execute('SELECT * FROM saved_songs WHERE user_id=? AND song_id=?',(session['user_id'],song_id)).fetchone()
    if existing:
        db.execute('DELETE FROM saved_songs WHERE user_id=? AND song_id=?',(session['user_id'],song_id))
        saved = False
    else:
        db.execute('INSERT INTO saved_songs(user_id,song_id) VALUES(?,?)',(session['user_id'],song_id))
        saved = True
    db.commit(); db.close()
    return jsonify({'saved': saved})

@app.route('/api/is_saved/<int:song_id>')
@login_required
def is_saved(song_id):
    db = get_db()
    r = db.execute('SELECT id FROM saved_songs WHERE user_id=? AND song_id=?',(session['user_id'],song_id)).fetchone()
    db.close()
    return jsonify({'saved': r is not None})

@app.route('/api/add_to_playlist', methods=['POST'])
@login_required
def add_to_playlist():
    data = request.get_json()
    pid, sid = data.get('playlist_id'), data.get('song_id')
    db = get_db()
    pl = db.execute('SELECT * FROM playlists WHERE id=? AND user_id=?',(pid,session['user_id'])).fetchone()
    if pl:
        try:
            db.execute('INSERT INTO playlist_songs(playlist_id,song_id) VALUES(?,?)',(pid,sid))
            db.commit()
            db.close()
            return jsonify({'ok':True})
        except: pass
    db.close()
    return jsonify({'ok':False})

@app.route('/api/remove_from_playlist', methods=['POST'])
@login_required
def remove_from_playlist():
    data = request.get_json()
    pid, sid = data.get('playlist_id'), data.get('song_id')
    db = get_db()
    db.execute('DELETE FROM playlist_songs WHERE playlist_id=? AND song_id=?',(pid,sid))
    db.commit(); db.close()
    return jsonify({'ok':True})

@app.route('/api/user_playlists')
@login_required
def user_playlists():
    db = get_db()
    pls = db.execute('SELECT id,name FROM playlists WHERE user_id=?',(session['user_id'],)).fetchall()
    db.close()
    return jsonify([dict(p) for p in pls])

# ─── ADMIN ROUTES ────────────────────────────────────────────────────────────

@app.route('/admin')
@admin_required
def admin_dashboard():
    db = get_db()
    stats = {
        'total_users': db.execute('SELECT COUNT(*) FROM users').fetchone()[0],
        'active_users': db.execute('SELECT COUNT(*) FROM users WHERE is_banned=0').fetchone()[0],
        'banned_users': db.execute('SELECT COUNT(*) FROM users WHERE is_banned=1').fetchone()[0],
        'total_songs': db.execute('SELECT COUNT(*) FROM songs').fetchone()[0],
        'total_albums': db.execute('SELECT COUNT(*) FROM albums').fetchone()[0],
        'total_plays': db.execute('SELECT COALESCE(SUM(plays),0) FROM songs').fetchone()[0],
        'total_playlists': db.execute('SELECT COUNT(*) FROM playlists').fetchone()[0],
    }
    recent_logins = db.execute('''SELECT * FROM login_logs ORDER BY timestamp DESC LIMIT 15''').fetchall()
    online_users = db.execute('''SELECT u.username,u.last_login FROM users u
        WHERE u.last_login IS NOT NULL ORDER BY u.last_login DESC LIMIT 10''').fetchall()
    top_songs = db.execute('SELECT * FROM songs ORDER BY plays DESC LIMIT 5').fetchall()
    db.close()
    return render_template('admin/dashboard.html', stats=stats, recent_logins=recent_logins,
                           online_users=online_users, top_songs=top_songs)

@app.route('/admin/songs')
@admin_required
def admin_songs():
    db = get_db()
    songs = db.execute('''SELECT s.*,g.name as genre_name,a.title as album_title
        FROM songs s LEFT JOIN genres g ON s.genre_id=g.id LEFT JOIN albums a ON s.album_id=a.id
        ORDER BY s.created_at DESC''').fetchall()
    genres = db.execute('SELECT * FROM genres').fetchall()
    albums = db.execute('SELECT * FROM albums').fetchall()
    db.close()
    return render_template('admin/songs.html', songs=songs, genres=genres, albums=albums)

@app.route('/admin/upload_song', methods=['POST'])
@admin_required
def upload_song():
    title = request.form['title']
    artist = request.form['artist']
    genre_id = request.form.get('genre_id') or None
    album_id = request.form.get('album_id') or None

    audio = request.files.get('audio')
    cover = request.files.get('cover')

    if not audio or not allowed_audio(audio.filename):
        flash('Invalid audio file.','error')
        return redirect(url_for('admin_songs'))

    audio_fn = save_file(audio, MUSIC_FOLDER)
    cover_fn = save_file(cover, COVER_FOLDER) if cover and allowed_image(cover.filename) else 'default_cover.jpg'

    db = get_db()
    db.execute('INSERT INTO songs(title,artist,genre_id,album_id,file_path,cover) VALUES(?,?,?,?,?,?)',
               (title,artist,genre_id,album_id,'uploads/music/'+audio_fn,'uploads/covers/'+cover_fn))
    db.commit(); db.close()
    flash('Song uploaded!','success')
    return redirect(url_for('admin_songs'))

@app.route('/admin/delete_song/<int:sid>', methods=['POST'])
@admin_required
def delete_song(sid):
    db = get_db()
    song = db.execute('SELECT * FROM songs WHERE id=?',(sid,)).fetchone()
    if song:
        fp = os.path.join(BASE_DIR,'static',song['file_path'])
        if os.path.exists(fp): os.remove(fp)
        db.execute('DELETE FROM playlist_songs WHERE song_id=?',(sid,))
        db.execute('DELETE FROM saved_songs WHERE song_id=?',(sid,))
        db.execute('DELETE FROM songs WHERE id=?',(sid,))
        db.commit()
    db.close()
    flash('Song deleted.','success')
    return redirect(url_for('admin_songs'))

@app.route('/admin/albums')
@admin_required
def admin_albums():
    db = get_db()
    albums = db.execute('''SELECT a.*,g.name as genre_name,
        (SELECT COUNT(*) FROM songs WHERE album_id=a.id) as song_count
        FROM albums a LEFT JOIN genres g ON a.genre_id=g.id ORDER BY a.created_at DESC''').fetchall()
    genres = db.execute('SELECT * FROM genres').fetchall()
    db.close()
    return render_template('admin/albums.html', albums=albums, genres=genres)

@app.route('/admin/add_album', methods=['POST'])
@admin_required
def add_album():
    title = request.form['title']
    artist = request.form['artist']
    genre_id = request.form.get('genre_id') or None
    description = request.form.get('description','')
    release_year = request.form.get('release_year') or None
    cover = request.files.get('cover')
    cover_fn = save_file(cover, COVER_FOLDER) if cover and allowed_image(cover.filename) else 'default_cover.jpg'
    db = get_db()
    db.execute('INSERT INTO albums(title,artist,genre_id,cover,description,release_year) VALUES(?,?,?,?,?,?)',
               (title,artist,genre_id,'uploads/covers/'+cover_fn,description,release_year))
    db.commit(); db.close()
    flash('Album added!','success')
    return redirect(url_for('admin_albums'))

@app.route('/admin/delete_album/<int:aid>', methods=['POST'])
@admin_required
def delete_album(aid):
    db = get_db()
    db.execute('UPDATE songs SET album_id=NULL WHERE album_id=?',(aid,))
    db.execute('DELETE FROM albums WHERE id=?',(aid,))
    db.commit(); db.close()
    flash('Album deleted.','success')
    return redirect(url_for('admin_albums'))

@app.route('/admin/users')
@admin_required
def admin_users():
    db = get_db()
    users = db.execute('''SELECT u.*,
        (SELECT COUNT(*) FROM playlists WHERE user_id=u.id) as playlist_count,
        (SELECT COUNT(*) FROM saved_songs WHERE user_id=u.id) as saved_count
        FROM users u ORDER BY u.created_at DESC''').fetchall()
    login_counts = db.execute('''SELECT username, COUNT(*) as cnt FROM login_logs
        WHERE action='login' GROUP BY username''').fetchall()
    lc = {r['username']:r['cnt'] for r in login_counts}
    db.close()
    return render_template('admin/users.html', users=users, login_counts=lc)

@app.route('/admin/ban_user/<int:uid>', methods=['POST'])
@admin_required
def ban_user(uid):
    action = request.form.get('action','ban')
    db = get_db()
    db.execute('UPDATE users SET is_banned=? WHERE id=?',(1 if action=='ban' else 0, uid))
    db.commit(); db.close()
    flash(f'User {"banned" if action=="ban" else "unbanned"}.','success')
    return redirect(url_for('admin_users'))

@app.route('/admin/logs')
@admin_required
def admin_logs():
    db = get_db()
    logs = db.execute('SELECT * FROM login_logs ORDER BY timestamp DESC LIMIT 100').fetchall()
    db.close()
    return render_template('admin/logs.html', logs=logs)

if __name__ == '__main__':
    os.makedirs(MUSIC_FOLDER, exist_ok=True)
    os.makedirs(COVER_FOLDER, exist_ok=True)
    os.makedirs(AVATAR_FOLDER, exist_ok=True)
    init_db()
    app.run(debug=True, port=5000)
