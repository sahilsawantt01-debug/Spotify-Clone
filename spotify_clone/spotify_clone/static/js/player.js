// ── SPOTIFY CLONE PLAYER ──
const audio = new Audio();
let currentSongId = null;
let playlist = [];
let currentIdx = 0;
let isPlaying = false;

audio.volume = 0.8;

function playSong(songId, songList) {
  if (songList && songList.length) {
    playlist = songList;
    currentIdx = songList.indexOf(songId);
    if (currentIdx === -1) currentIdx = 0;
  }
  fetch(`/api/play/${songId}`)
    .then(r => r.json())
    .then(data => {
      currentSongId = songId;
      audio.src = `/static/${data.file}`;
      audio.play();
      isPlaying = true;
      updatePlayerUI(data);
      updatePlayPauseBtn();
      checkIfSaved(songId);
    });
}

function updatePlayerUI(data) {
  document.getElementById('playerTitle').textContent = data.title;
  document.getElementById('playerArtist').textContent = data.artist;
  const coverSrc = data.cover && data.cover !== 'default_cover.jpg'
    ? `/static/${data.cover}`
    : `/static/uploads/covers/default_cover.jpg`;
  document.getElementById('playerCover').src = coverSrc;
  document.getElementById('playerBar').style.borderTop = '2px solid #1DB954';
}

function updatePlayPauseBtn() {
  const btn = document.getElementById('playPauseBtn');
  btn.innerHTML = isPlaying
    ? '<i class="fas fa-pause"></i>'
    : '<i class="fas fa-play"></i>';
}

function togglePlay() {
  if (!currentSongId) return;
  if (isPlaying) { audio.pause(); isPlaying = false; }
  else { audio.play(); isPlaying = true; }
  updatePlayPauseBtn();
}

function nextSong() {
  if (!playlist.length) return;
  currentIdx = (currentIdx + 1) % playlist.length;
  playSong(playlist[currentIdx]);
}

function prevSong() {
  if (!playlist.length) return;
  if (audio.currentTime > 3) { audio.currentTime = 0; return; }
  currentIdx = (currentIdx - 1 + playlist.length) % playlist.length;
  playSong(playlist[currentIdx]);
}

function seek(val) {
  if (audio.duration) audio.currentTime = (val / 100) * audio.duration;
}

function setVolume(val) {
  audio.volume = val / 100;
}

function checkIfSaved(sid) {
  fetch(`/api/is_saved/${sid}`).then(r => r.json()).then(d => {
    const btn = document.getElementById('playerHeartBtn');
    if (btn) btn.innerHTML = d.saved
      ? '<i class="fas fa-heart" style="color:#1DB954"></i>'
      : '<i class="far fa-heart"></i>';
  });
}

function formatTime(s) {
  const m = Math.floor(s / 60);
  const sec = Math.floor(s % 60);
  return `${m}:${sec.toString().padStart(2, '0')}`;
}

audio.addEventListener('timeupdate', () => {
  if (audio.duration) {
    const pct = (audio.currentTime / audio.duration) * 100;
    document.getElementById('progressBar').value = pct;
    document.getElementById('currentTime').textContent = formatTime(audio.currentTime);
    document.getElementById('totalTime').textContent = formatTime(audio.duration);
  }
});

audio.addEventListener('ended', () => {
  nextSong();
});

audio.addEventListener('error', () => {
  console.error('Audio error:', audio.error);
  isPlaying = false;
  updatePlayPauseBtn();
});

// Keyboard shortcuts
document.addEventListener('keydown', e => {
  if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
  if (e.code === 'Space') { e.preventDefault(); togglePlay(); }
  if (e.code === 'ArrowRight') { audio.currentTime = Math.min(audio.currentTime + 10, audio.duration); }
  if (e.code === 'ArrowLeft') { audio.currentTime = Math.max(audio.currentTime - 10, 0); }
});
