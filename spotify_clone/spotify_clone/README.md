# 🎵 Spotify Clone

A full-featured Spotify-like music streaming web app built with Python (Flask) and SQLite.

---

## 🚀 Features

### User Features
- Register / Login / Logout
- Browse music by genre categories
- Search songs, albums, artists
- Play music with full audio player (prev/next/seek/volume)
- Like/Save songs to library
- Create and manage playlists
- Add/Remove songs from playlists
- Browse albums

### Admin Features
- Fixed admin login (username: `admin`, password: `admin123`)
- Upload new songs (mp3, wav, ogg, m4a, flac)
- Delete songs
- Add/Delete albums
- View all registered users
- See login count per user
- Ban / Unban users
- View all login activity logs
- Dashboard with live stats

---

## 📦 Setup Instructions

### 1. Install Python
Make sure Python 3.8+ is installed on your system.

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the app
```bash
python app.py
```

### 4. Open in browser
```
http://localhost:5000
```

---

## 🔑 Login Credentials

| Role  | Username | Password |
|-------|----------|----------|
| Admin | admin    | admin123 |
| User  | Register via signup page |

---

## 📁 Project Structure

```
spotify_clone/
├── app.py                  # Main Flask application
├── spotify.db              # SQLite database (auto-created)
├── requirements.txt
├── README.md
├── templates/
│   ├── base.html           # Base layout (sidebar, player, modals)
│   ├── login.html
│   ├── register.html
│   ├── home.html
│   ├── search.html
│   ├── genre.html
│   ├── album.html
│   ├── library.html
│   ├── playlist.html
│   └── admin/
│       ├── dashboard.html
│       ├── songs.html
│       ├── albums.html
│       ├── users.html
│       └── logs.html
└── static/
    ├── css/
    │   └── style.css
    ├── js/
    │   └── player.js
    └── uploads/
        ├── music/          # Uploaded audio files
        ├── covers/         # Album/song cover images
        └── avatars/        # User avatars
```

---

## 🎨 Tech Stack

- **Backend:** Python, Flask, SQLite
- **Frontend:** HTML5, CSS3, Vanilla JavaScript
- **Audio:** HTML5 Audio API
- **Icons:** Font Awesome 6
- **Fonts:** Google Fonts (Inter)

---

## 📝 Notes

- The database (`spotify.db`) is auto-created on first run
- 15 music genres are pre-seeded
- Uploaded files are stored in `static/uploads/`
- Keyboard shortcuts: `Space` = play/pause, `←/→` = seek 10s
- Banned users cannot log in
