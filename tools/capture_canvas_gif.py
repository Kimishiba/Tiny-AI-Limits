#!/usr/bin/env python3
"""
Pixel-perfect capture of GC9A01 Canvas animation from emulator/index.html using Headless Chrome.
"""

import http.server
import socketserver
import subprocess
import threading
import time
import base64
import os
import json
from PIL import Image
import io

PORT = 8998
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
captured_frames = []
server_done = threading.Event()

# HTML page that runs the exact canvas code and posts frames to server
HTML_PAGE = """<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Anybody:wght@800;900&family=JetBrains+Mono:wght@700;800;900&display=swap" rel="stylesheet">
  <style>
    body { background: #000; margin: 0; padding: 0; overflow: hidden; }
    canvas { display: block; width: 240px; height: 240px; }
  </style>
</head>
<body>
  <canvas id="screenCanvas" width="240" height="240"></canvas>
  <script>
    window.addEventListener('load', async () => {
      // Ensure Google Fonts are loaded
      await document.fonts.ready;
      
      const canvas = document.getElementById('screenCanvas');
      const c = canvas.getContext('2d');
      const cx = 120, cy = 120, rScreen = 114;

      function drawCurvedTextClockwise(ctx, text, centerX, centerY, radius, centerAngleRad, color, font) {
        ctx.save();
        ctx.font = font;
        ctx.fillStyle = color;
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";

        const charWidths = [];
        let totalWidth = 0;
        for (let i = 0; i < text.length; i++) {
          const w = ctx.measureText(text[i]).width * 1.12;
          charWidths.push(w);
          totalWidth += w;
        }

        const totalAngle = totalWidth / radius;
        let currentAngle = centerAngleRad - totalAngle / 2;

        for (let i = 0; i < text.length; i++) {
          const ch = text[i];
          const chAngle = charWidths[i] / radius;
          const midAngle = currentAngle + chAngle / 2;

          ctx.save();
          ctx.translate(centerX, centerY);
          ctx.rotate(midAngle);
          ctx.translate(0, -radius);
          ctx.fillText(ch, 0, 0);
          ctx.restore();

          currentAngle += chAngle;
        }
        ctx.restore();
      }

      function drawHingeBracket(posX, midY, cardW) {
        function drawSingle(hx) {
          const bw = 5, bh = 12;
          const bx = hx - bw / 2, by = midY - bh / 2;
          c.fillStyle = "#12151f";
          c.beginPath();
          c.roundRect(bx, by, bw, bh, 2);
          c.fill();
          c.strokeStyle = "#384058";
          c.lineWidth = 1.0;
          c.stroke();
          c.fillStyle = "#8a96ab";
          c.fillRect(bx + 1, midY - 2.5, bw - 2, 5);
          c.fillStyle = "#dce3f2";
          c.fillRect(bx + 1, midY - 2.5, bw - 2, 1);
          c.fillStyle = "#252b3b";
          c.fillRect(bx + 1, midY + 1.5, bw - 2, 1);
        }
        drawSingle(posX);
        drawSingle(posX + cardW);
      }

      function drawFlipCard(posX, posY, oldDigit, newDigit, progress) {
        const cardW = 48, cardH = 72;
        const midY = posY + cardH / 2;
        const halfH = cardH / 2;
        const numFont = "900 64px 'Anybody', 'JetBrains Mono', sans-serif";

        const COLOR_TOP_FRONT = "#222633";
        const COLOR_BOT_BACK  = "#12141c";
        const COLOR_CARD_BORDER = "#2b3042";

        c.fillStyle = COLOR_BOT_BACK;
        c.beginPath();
        c.roundRect(posX, posY, cardW, cardH, 8);
        c.fill();
        c.strokeStyle = COLOR_CARD_BORDER;
        c.lineWidth = 1.2;
        c.stroke();

        if (progress >= 1.0 || oldDigit === newDigit) {
          // Top Half
          c.save();
          c.beginPath();
          c.roundRect(posX, posY, cardW, halfH, [8, 8, 0, 0]);
          c.clip();
          c.fillStyle = COLOR_TOP_FRONT;
          c.fillRect(posX, posY, cardW, halfH);
          c.save();
          c.translate(posX + cardW / 2, posY + cardH / 2 + 3.5);
          c.scale(0.92, 1.25);
          c.font = numFont;
          c.fillStyle = "#ffffff";
          c.textAlign = "center";
          c.textBaseline = "middle";
          c.fillText(newDigit, 0, 0);
          c.restore();
          c.restore();

          // Bottom Half
          c.save();
          c.beginPath();
          c.roundRect(posX, midY, cardW, halfH, [0, 0, 8, 8]);
          c.clip();
          c.fillStyle = COLOR_BOT_BACK;
          c.fillRect(posX, midY, cardW, halfH);
          c.save();
          c.translate(posX + cardW / 2, posY + cardH / 2 + 3.5);
          c.scale(0.92, 1.25);
          c.font = numFont;
          c.fillStyle = "#eceef4";
          c.textAlign = "center";
          c.textBaseline = "middle";
          c.fillText(newDigit, 0, 0);
          c.restore();
          c.restore();
        } else {
          // 3D Flip
          c.save();
          c.beginPath();
          c.roundRect(posX, posY, cardW, halfH, [8, 8, 0, 0]);
          c.clip();
          c.fillStyle = COLOR_TOP_FRONT;
          c.fillRect(posX, posY, cardW, halfH);
          c.save();
          c.translate(posX + cardW / 2, posY + cardH / 2 + 3.5);
          c.scale(0.92, 1.25);
          c.font = numFont;
          c.fillStyle = "#ffffff";
          c.textAlign = "center";
          c.textBaseline = "middle";
          c.fillText(newDigit, 0, 0);
          c.restore();
          c.restore();

          c.save();
          c.beginPath();
          c.roundRect(posX, midY, cardW, halfH, [0, 0, 8, 8]);
          c.clip();
          c.fillStyle = COLOR_BOT_BACK;
          c.fillRect(posX, midY, cardW, halfH);
          c.save();
          c.translate(posX + cardW / 2, posY + cardH / 2 + 3.5);
          c.scale(0.92, 1.25);
          c.font = numFont;
          c.fillStyle = "#eceef4";
          c.textAlign = "center";
          c.textBaseline = "middle";
          c.fillText(oldDigit, 0, 0);
          c.restore();
          c.restore();

          if (progress < 0.5) {
            const scale = Math.cos(progress * Math.PI);
            const flapH = Math.max(0.1, halfH * scale);
            const flapY = midY - flapH;
            c.save();
            c.beginPath();
            c.rect(posX, flapY, cardW, flapH);
            c.clip();
            c.fillStyle = COLOR_TOP_FRONT;
            c.fillRect(posX, flapY, cardW, flapH);
            c.save();
            c.translate(posX + cardW / 2, midY);
            c.scale(0.92, scale * 1.25);
            c.font = numFont;
            c.fillStyle = "#ffffff";
            c.textAlign = "center";
            c.textBaseline = "middle";
            c.fillText(oldDigit, 0, -halfH / 2 + 3.5);
            c.restore();
            c.fillStyle = "rgba(0, 0, 0, " + (progress * 0.85).toFixed(2) + ")";
            c.fillRect(posX, flapY, cardW, flapH);
            c.restore();
          } else {
            const scale = -Math.cos(progress * Math.PI);
            const flapH = Math.max(0.1, halfH * scale);
            c.save();
            c.beginPath();
            c.rect(posX, midY, cardW, flapH);
            c.clip();
            c.fillStyle = COLOR_BOT_BACK;
            c.fillRect(posX, midY, cardW, flapH);
            c.save();
            c.translate(posX + cardW / 2, midY);
            c.scale(0.92, scale * 1.25);
            c.font = numFont;
            c.fillStyle = "#eceef4";
            c.textAlign = "center";
            c.textBaseline = "middle";
            c.fillText(newDigit, 0, halfH / 2 + 3.5);
            c.restore();
            c.fillStyle = "rgba(0, 0, 0, " + ((1.0 - progress) * 0.85).toFixed(2) + ")";
            c.fillRect(posX, midY, cardW, flapH);
            c.restore();
          }
        }

        c.fillStyle = "#06070a";
        c.fillRect(posX, midY - 1, cardW, 1.5);
        c.fillStyle = "#343a4e";
        c.fillRect(posX, midY + 0.5, cardW, 0.8);

        drawHingeBracket(posX, midY, cardW);
      }

      function renderFrame(state) {
        c.clearRect(0, 0, 240, 240);

        // 1. Bezel Ring
        if (state.waiting_for_input) {
          c.strokeStyle = "#241804";
          c.lineWidth = 6;
          c.beginPath();
          c.arc(cx, cy, rScreen + 3, 0, Math.PI * 2);
          c.stroke();

          c.save();
          c.translate(cx, cy);
          c.rotate(state.spinAngle);
          c.strokeStyle = "#FFB800";
          c.lineWidth = 5;
          c.lineCap = "round";
          c.setLineDash([34, 14, 12, 14, 46, 18, 16, 14]);
          c.beginPath();
          c.arc(0, 0, rScreen + 3, 0, Math.PI * 2);
          c.stroke();
          c.setLineDash([]);
          c.restore();
        } else {
          c.strokeStyle = "#1f2330";
          c.lineWidth = 6;
          c.beginPath();
          c.arc(cx, cy, rScreen + 3, 0, Math.PI * 2);
          c.stroke();
        }

        // Screen background
        c.fillStyle = "#000000";
        c.beginPath();
        c.arc(cx, cy, rScreen, 0, Math.PI * 2);
        c.fill();

        // 2. Curved inside quota labels
        const textRadius = 86.5;
        const badgeFont = "900 10.5px 'JetBrains Mono', 'Fira Code', monospace";
        drawCurvedTextClockwise(c, "CLAUDE " + state.claudePct + "%", cx, cy, textRadius, -Math.PI / 2, "#00E5FF", badgeFont);
        drawCurvedTextClockwise(c, "ANTIGRAVITY " + state.antiPct + "%", cx, cy, textRadius, Math.PI / 2, "#FF7A00", badgeFont);

        // 3. Top Crown LED & Rain Indicator
        const ledY = cy - 105;
        c.save();
        c.fillStyle = "#12151f";
        c.beginPath();
        c.arc(cx, ledY, 3.5, 0, Math.PI * 2);
        c.fill();
        c.fillStyle = "#22c55e";
        c.shadowColor = "rgba(34, 197, 94, 0.6)";
        c.shadowBlur = 6;
        c.beginPath();
        c.arc(cx, ledY, 2.2, 0, Math.PI * 2);
        c.fill();
        c.restore();

        c.font = "bold 11px 'JetBrains Mono', 'Fira Code', monospace";
        c.textAlign = "center";
        c.textBaseline = "middle";
        c.fillStyle = (state.hours_until_rain <= 3) ? "#38bdf8" : "#cbd5e1";
        c.fillText("RAIN IN " + state.hours_until_rain + "h", cx, cy - 93);

        // 4. Dual Side Radial Arcs
        const arcR = 105, innerArcR = 96;
        c.lineCap = "round";

        const bottomAngleLeft = 0.70 * Math.PI, topAngleLeft = 1.30 * Math.PI;
        const totalSweepLeft = topAngleLeft - bottomAngleLeft;
        c.lineWidth = 7; c.strokeStyle = "rgba(0, 229, 255, 0.16)";
        c.beginPath(); c.arc(cx, cy, arcR, bottomAngleLeft, topAngleLeft, false); c.stroke();
        c.lineWidth = 2; c.strokeStyle = "rgba(0, 229, 255, 0.22)";
        c.beginPath(); c.arc(cx, cy, innerArcR, bottomAngleLeft, topAngleLeft, false); c.stroke();

        if (state.claudePct > 0) {
          const activeEndLeft = bottomAngleLeft + (state.claudePct / 100) * totalSweepLeft;
          c.lineWidth = 7; c.strokeStyle = "#00E5FF";
          c.beginPath(); c.arc(cx, cy, arcR, bottomAngleLeft, activeEndLeft, false); c.stroke();
          c.lineWidth = 2;
          c.beginPath(); c.arc(cx, cy, innerArcR, bottomAngleLeft, activeEndLeft, false); c.stroke();
        }

        const bottomAngleRight = 0.30 * Math.PI, totalSweepRight = 0.60 * Math.PI;
        c.lineWidth = 7; c.strokeStyle = "rgba(255, 122, 0, 0.16)";
        c.beginPath(); c.arc(cx, cy, arcR, bottomAngleRight, bottomAngleRight - totalSweepRight, true); c.stroke();
        c.lineWidth = 2; c.strokeStyle = "rgba(255, 122, 0, 0.22)";
        c.beginPath(); c.arc(cx, cy, innerArcR, bottomAngleRight, bottomAngleRight - totalSweepRight, true); c.stroke();

        if (state.antiPct > 0) {
          const activeEndRight = bottomAngleRight - (state.antiPct / 100) * totalSweepRight;
          c.lineWidth = 7; c.strokeStyle = "#FF7A00";
          c.beginPath(); c.arc(cx, cy, arcR, bottomAngleRight, activeEndRight, true); c.stroke();
          c.lineWidth = 2;
          c.beginPath(); c.arc(cx, cy, innerArcR, bottomAngleRight, activeEndRight, true); c.stroke();
        }

        // 5. 2x2 Matrix Flip Cards
        const cardW = 48, cardH = 72, gap = 6;
        const x1 = cx - cardW - gap / 2, x2 = cx + gap / 2;
        const yTop = cy - cardH - gap / 2, yBottom = cy + gap / 2;

        drawFlipCard(x1, yTop, state.digits[0], state.digits[0], 1.0);
        drawFlipCard(x2, yTop, state.digits[1], state.digits[1], 1.0);
        drawFlipCard(x1, yBottom, state.digits[2], state.digits[2], 1.0);
        drawFlipCard(x2, yBottom, state.oldDigitM2, state.digits[3], state.flipProg);

        // 6. Bottom Sub-HUD
        if (state.waiting_for_input) {
          c.font = "bold 10px 'JetBrains Mono', monospace";
          c.fillStyle = state.blinkState ? "#FFB800" : "#996e00";
          c.fillText("⚠️ AGENT ALERT", cx, cy + 81);
          c.font = "bold 11px 'JetBrains Mono', monospace";
          c.fillStyle = "#ffffff";
          c.fillText("APPROVE PLAN", cx, cy + 95);
        } else {
          c.font = "bold 10px 'JetBrains Mono', 'Fira Code', monospace";
          c.fillStyle = "#94a3b8";
          c.fillText("FRI AUG 21", cx, cy + 81);
          c.font = "900 13px 'JetBrains Mono', 'Anybody', monospace";
          c.fillStyle = "#ffffff";
          c.fillText("23.5°C ☀️", cx, cy + 95);
        }
      }

      // Generate all animation sequence frames
      const totalFrames = 42;
      for (let f = 0; f < totalFrames; f++) {
        let state;
        if (f < 24) {
          const t = f / 23.0;
          state = {
            claudePct: Math.round(24 + t * 44),
            antiPct: Math.round(12 + t * 30),
            hours_until_rain: 3,
            digits: [1, 4, 3, f >= 12 ? 3 : 2],
            oldDigitM2: 2,
            flipProg: f < 12 ? 1.0 : Math.min(1.0, (f - 12) / 8.0),
            waiting_for_input: false
          };
        } else {
          const af = f - 24;
          state = {
            claudePct: 68,
            antiPct: 42,
            hours_until_rain: 3,
            digits: [1, 4, 3, 3],
            oldDigitM2: 3,
            flipProg: 1.0,
            waiting_for_input: true,
            spinAngle: (af * 0.42),
            blinkState: (af % 4 < 2)
          };
        }

        renderFrame(state);
        const dataUrl = canvas.toDataURL('image/png');
        await fetch('/save_frame', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ index: f, data: dataUrl })
        });
      }

      // Signal completion
      await fetch('/done', { method: 'POST' });
    });
  </script>
</body>
</html>
"""

class FrameHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path in ['/', '/render.html']:
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode('utf-8'))
        else:
            super().do_GET()

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)

        if self.path == '/save_frame':
            payload = json.loads(post_data.decode('utf-8'))
            idx = payload['index']
            b64_data = payload['data'].split(',')[1]
            img_bytes = base64.b64decode(b64_data)
            im = Image.open(io.BytesIO(img_bytes)).convert('RGB')
            captured_frames.append((idx, im))
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'OK')
        elif self.path == '/done':
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'DONE')
            server_done.set()

def run_server():
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), FrameHandler) as httpd:
        while not server_done.is_set():
            httpd.handle_request()

def main():
    print(f"Starting frame capture server on port {PORT}...")
    t = threading.Thread(target=run_server, daemon=True)
    t.start()

    print("Launching Headless Chrome for pixel-perfect Canvas rendering...")
    chrome_proc = subprocess.Popen([
        CHROME_PATH,
        "--headless=new",
        "--disable-gpu",
        "--hide-scrollbars",
        f"--window-size=240,240",
        f"http://localhost:{PORT}/render.html"
    ])

    server_done.wait(timeout=20)
    chrome_proc.terminate()

    print(f"Captured {len(captured_frames)} pixel-perfect frames from Chrome Canvas!")
    if not captured_frames:
        print("[ERROR] No frames captured.")
        return

    # Sort frames
    captured_frames.sort(key=lambda x: x[0])
    frames = [f[1] for f in captured_frames]

    durations = [85] * 24 + [110] * (len(frames) - 24)

    output_path = "round 240x240/assets/gc9a01_round_display_demo.gif"
    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        optimize=True
    )
    print(f"[SUCCESS] Pixel-perfect GC9A01 animated demonstration GIF saved to {output_path}!")

if __name__ == "__main__":
    main()
