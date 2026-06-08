#!/usr/bin/env python3
"""
Spotify Clone - Startup Script
Run this file to start the application.
"""

import os
import sys

def main():
    # Try to import Flask
    try:
        import flask
        import werkzeug
    except ImportError:
        print("Installing dependencies...")
        os.system(f"{sys.executable} -m pip install flask werkzeug")

    # Set up directories
    base = os.path.dirname(os.path.abspath(__file__))
    for d in ['static/uploads/music', 'static/uploads/covers', 'static/uploads/avatars']:
        os.makedirs(os.path.join(base, d), exist_ok=True)

    # Create default cover if missing
    cover_path = os.path.join(base, 'static/uploads/covers/default_cover.jpg')
    if not os.path.exists(cover_path):
        import struct, zlib
        def create_png(w, h, r, g, b):
            def chunk(ct, d):
                c = struct.pack('>I', len(d)) + ct + d
                return c + struct.pack('>I', zlib.crc32(ct + d) & 0xffffffff)
            hdr = b'\x89PNG\r\n\x1a\n'
            ihdr = chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
            raw = []
            for y in range(h):
                row = b'\x00'
                for x in range(w):
                    f = (x+y)/(w+h)
                    row += bytes([max(0,int(r*(1-f*.4))), max(0,int(g*(1-f*.4))), max(0,int(b*(1-f*.4)))])
                raw.append(row)
            idat = chunk(b'IDAT', zlib.compress(b''.join(raw), 6))
            iend = chunk(b'IEND', b'')
            return hdr + ihdr + idat + iend
        with open(cover_path, 'wb') as f:
            f.write(create_png(300, 300, 30, 185, 84))

    # Initialize DB and run
    from app import app, init_db
    init_db()

    print("\n" + "="*50)
    print("  🎵 Spotify Clone is running!")
    print("="*50)
    print("  URL:      http://localhost:5000")
    print("  Admin:    username=admin  password=admin123")
    print("  Users:    Register at /register")
    print("="*50 + "\n")

    app.run(debug=False, host='0.0.0.0', port=5000)

if __name__ == '__main__':
    main()
