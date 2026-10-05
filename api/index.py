import secrets
import time
from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse

app = FastAPI()

# In-memory store: {token: {"text": payload, "expiry": timestamp, "views_left": count}}
SECRETS = {}

@app.get("/", response_class=HTMLResponse)
def index():
    return """
    <!DOCTYPE html>
    <html>
    <body style="font-family:sans-serif; padding:2rem; background:#111; color:#eee;">
      <h2>Upload Secret</h2>
      <form action="/upload" method="post">
        <textarea name="payload" rows="12" style="width:100%; font-family:monospace; background:#222; color:#fff; border:1px solid #444; padding:0.5rem;" placeholder="Paste code here..." required></textarea><br><br>
        
        <label>Time Limit:</label>
        <select name="ttl" style="padding:0.5rem; background:#222; color:#fff; border:1px solid #444; margin-right: 1rem;">
          <option value="60">1 minute</option>
          <option value="300" selected>5 minutes</option>
          <option value="600">10 minutes</option>
          <option value="3600">1 hour</option>
          <option value="86400">1 day</option>
        </select>

        <label>Opening Limit:</label>
        <select name="views" style="padding:0.5rem; background:#222; color:#fff; border:1px solid #444;">
          <option value="1" selected>1 time</option>
          <option value="2">2 times</option>
          <option value="3">3 times</option>
        </select><br><br>

        <button type="submit" style="padding:0.75rem 1.5rem; cursor:pointer; background:#fff; color:#000; border:none; font-weight:bold;">Generate URL</button>
      </form>
    </body>
    </html>
    """

@app.post("/upload", response_class=HTMLResponse)
def upload(payload: str = Form(...), ttl: int = Form(300), views: int = Form(1)):
    token = secrets.token_urlsafe(32)  # High-entropy unguessable token
    SECRETS[token] = {
        "text": payload,
        "expiry": time.time() + ttl,
        "views_left": views
    }
    
    # Normally you'd want to use the request's base URL, but for relative paths this is fine
    one_time_url = f"/view/{token}"
    
    return f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family:sans-serif; padding:2rem; background:#111; color:#eee;">
      <h3>Secure URL Created</h3>
      <p>This link will self-destruct after <strong>{views} view(s)</strong> or when its time limit expires.</p>
      <input style="width:100%; padding:0.5rem; font-family:monospace; background:#222; color:#fff; border:1px solid #444;" value="{one_time_url}" readonly onclick="this.select();">
      <br><br>
      <a href="/" style="color:#4da6ff;">Create another</a>
    </body>
    </html>
    """

@app.get("/view/{token}", response_class=HTMLResponse)
def view_and_burn(token: str):
    entry = SECRETS.get(token)
    
    if not entry or time.time() > entry["expiry"]:
        SECRETS.pop(token, None)
        raise HTTPException(status_code=404, detail="Secret has expired or does not exist.")

    secret_text = entry["text"]
    entry["views_left"] -= 1

    if entry["views_left"] <= 0:
        # Final view, burn it entirely
        SECRETS.pop(token, None)
    
    # Escape HTML to prevent injection
    import html
    escaped_text = html.escape(secret_text)

    return f"""
    <!DOCTYPE html>
    <html>
    <body style="margin:0; background:#1e1e1e;">
      <textarea id="box" readonly style="width:100vw; height:100vh; background:#1e1e1e; color:#fff; font-family:monospace; border:none; padding:1.5rem; box-sizing:border-box; outline:none; resize:none; font-size:14px;">{escaped_text}</textarea>
      <script>
        const b = document.getElementById('box');
        b.focus();
        b.select();
      </script>
    </body>
    </html>
    """
