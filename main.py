from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
import base64
import secrets
import random
import string
import json
import asyncio
from typing import Dict
from models import Homepage
import uuid

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Simulated user database
USERS = {
    "mark": "pass123",
    "luke": "pass456"
}

# Store active user sessions
user_sessions: Dict[str, Homepage] = {}

async def create_homepage(username: str) -> Homepage:
    """Create a new Homepage instance with initialized queue."""
    homepage = Homepage(username)
    # Initialize the queue in an async context
    homepage._update_queue = asyncio.Queue()
    return homepage

async def verify_credentials(username: str, password: str):
    """Verify user credentials and create/return Homepage instance."""
    if username in USERS and secrets.compare_digest(password, USERS[username]):
        if username not in user_sessions:
            user_sessions[username] = await create_homepage(username)
        return user_sessions[username]
    return None

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    auth_token = request.cookies.get("auth_token")
    if not auth_token:
        return RedirectResponse(url="/login")

    try:
        username = base64.b64decode(auth_token).decode().split(":")[0]
        user = user_sessions.get(username)
        user.sessionId = str(uuid.uuid4())
        if not user:
            return RedirectResponse(url="/login")
    except Exception:
        return RedirectResponse(url="/login")

    return templates.TemplateResponse("home.html", {"request": request, "user": user})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    user = await verify_credentials(username, password)
    if not user:
        return templates.TemplateResponse(
            "login.html", 
            {"request": request, "error": "Invalid credentials"}
        )

    auth_token = base64.b64encode(f"{username}:authenticated".encode()).decode()
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(
        key="auth_token",
        value=auth_token,
        httponly=True,
        max_age=1800,
        samesite="lax"
    )
    return response

@app.get("/logout")
async def logout(request: Request):
    auth_token = request.cookies.get("auth_token")
    if auth_token:
        try:
            username = base64.b64decode(auth_token).decode().split(":")[0]
            # Clean up the user session on logout
            user_sessions.pop(username, None)
        except Exception:
            pass
    
    response = RedirectResponse(url="/login")
    response.delete_cookie("auth_token")
    return response

@app.post("/add_post")
async def add_post(request: Request, post_content: str = Form(...)):
    auth_token = request.cookies.get("auth_token")
    if not auth_token:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    try:
        username = base64.b64decode(auth_token).decode().split(":")[0]
        user = user_sessions.get(username)
        if not user:
            return JSONResponse({"error": "Unauthorized"}, status_code=401)
    except Exception:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    # Add the new post
    user.add_post(post_content)
    
    # Generate HTML update for the posts list
    html = (
        f'<ol id="ol_{user.username}">' + 
        ''.join(f'<li>{post}</li>' for post in user.posts) + 
        '</ol>'
    )
    
    # Queue the HTML update
    await user.queue_update({"html": {f"ol_{user.username}": html}})
    
    # Queue the form reset JS command
    await user.queue_update({"js": {"exec": 'document.getElementById("addPostForm").reset();'}})
    
    return {"status": "success"}

@app.get("/generate_post")
async def generate_post(request: Request):
    auth_token = request.cookies.get("auth_token")
    if not auth_token:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    try:
        username = base64.b64decode(auth_token).decode().split(":")[0]
        user = user_sessions.get(username)
        if not user:
            return JSONResponse({"error": "Unauthorized"}, status_code=401)
    except Exception:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    # Toggle the button state
    user.btnPressed = not user.btnPressed
    # Create HTML update
    button_html = f''' <button id="btn_{ user.username }" onclick="fetch('/generate_post/')" type="button" disabled> Update HTML Element </button> '''
    # Queue the update
    await user.queue_update({   "html": {f"btn_{user.username}": button_html}       })

    for i in range(0,5):
        # Generate random string post
        random_post = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        # Add the post to user's data
        user.add_post(random_post)
        # Generate HTML update
        html = (
            f'<ol id="ol_{user.username}">' + 
            ''.join(f'<li>{post}</li>' for post in user.posts) + 
            '</ol>'
        )
        
        # Queue the update
        await user.queue_update({    "html": {f"ol_{user.username}": html}     })
        await asyncio.sleep(1)

    # Toggle the button state
    user.btnPressed = not user.btnPressed
    # Create HTML update
    button_html = f''' <button id="btn_{ user.username }" onclick="fetch('/generate_post/')" type="button" >Update HTML Element</button> '''
    # Queue the update
    await user.queue_update({   "html": {f"btn_{user.username}": button_html}       })

    return {"status": "success"}

@app.get("/stream/{username}")
async def message_stream(username: str):
    user = user_sessions.get(username)
    if not user:
        return JSONResponse({"error": "User not found"}, status_code=404)

    async def event_generator():
        try:
            while True:
                update = await user._update_queue.get()
                yield f"data: {json.dumps(update)}\n\n"
        except asyncio.CancelledError:
            # Handle disconnection
            pass

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Transfer-Encoding": "chunked"
        }
    )

@app.on_event("startup")
async def startup_event():
    """Initialize any async resources on startup."""
    pass

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up any async resources on shutdown."""
    user_sessions.clear()