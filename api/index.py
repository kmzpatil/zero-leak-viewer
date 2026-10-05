import secrets
import time
from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse

app = FastAPI()

# In-memory store: {token: (text, expiry_timestamp)}
SECRETS = {}
TTL_SECONDS = 600  # Burns after 10 minutes if unread

@app.get("/", response_class=HTMLResponse)
def index():
    return """
    <!DOCTYPE html>
    <html>
    <body style="font-family:sans-serif; padding:2rem; background:#111; color:#eee;">
      <h2>Upload Secret</h2>
      <form action="/upload" method="post">
        <textarea name="payload" rows="12" style="width:100%; font-family:monospace;" placeholder="Paste code here..."></textarea><br><br>
        <button type="submit" style="padding:0.75rem 1.5rem; cursor:pointer;">Generate One-Time URL</button>
      </form>
    </body>
    </html>
    """

@app.post("/upload", response_class=HTMLResponse)
def upload(payload: str = Form(...)):
    token = secrets.token_urlsafe(32)  # High-entropy unguessable token
    SECRETS[token] = (payload, time.time() + TTL_SECONDS)
    one_time_url = f"/view/{token}"
    return f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family:sans-serif; padding:2rem; background:#111; color:#eee;">
      <h3>One-Time URL Created</h3>
      <p>This link will self-destruct after the first page load:</p>
      <input style="width:100%; padding:0.5rem; font-family:monospace;" value="{one_time_url}" readonly onclick="this.select();">
    </body>
    </html>
    """

@app.get("/view/{token}", response_class=HTMLResponse)
def view_and_burn(token: str):
    entry = SECRETS.pop(token, None)  # Atomically pops and deletes
    
    if not entry or time.time() > entry[1]:
        raise HTTPException(status_code=404, detail="Secret has already expired or been burned.")

    secret_text = entry[0]
    
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
