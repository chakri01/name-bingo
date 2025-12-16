from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from datetime import datetime
import os
import random
import json
from database import get_db, engine
from models import Base, Name, Ticket, GameState, ClaimQueue
from tickets import pre_generate_tickets
from fastapi.staticfiles import StaticFiles
import os

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ENV VARS
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
JOIN_URL = os.getenv("JOIN_URL", "https://bingo-frontend-production.up.railway.app/join")

# After app creation, before routes
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR)
    os.makedirs(os.path.join(STATIC_DIR, "photos"))

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# -----------------------------
# BASIC ROUTES
# -----------------------------

@app.get("/")
async def root():
    return {"status": "ok", "message": "Name Bingo API Running"}

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": str(datetime.now())}

@app.get("/admin")
async def admin():
    return {
        "status": "ok",
        "message": "Admin endpoint",
        "available_endpoints": [
            "/api/admin/login",
            "/api/admin/pick-name",
            "/api/admin/claims",
            "/api/admin/verify-claim",
            "/api/admin/reset-game",
            "/api/admin/qr-code"
        ]
    }

@app.get("/api/names")
async def get_names(db: Session = Depends(get_db)):
    """Get all available (unassigned) names for autocomplete"""
    names = db.query(Name.name_text).filter(Name.is_picked == False).all()
    return {"names": [n[0] for n in names]}

# New endpoint to get profile data
@app.get("/api/profile/{name}")
async def get_profile(name: str):
    try:
        PROFILES_FILE = os.path.join(os.path.dirname(__file__), "profiles.json")
        
        if not os.path.exists(PROFILES_FILE):
            return {"photo": None, "bio": None, "blur": False}
        
        with open(PROFILES_FILE) as f:
            profiles = json.load(f)
        
        profile = profiles.get(name, {})
        return {
            "photo": profile.get("photo"),
            "bio": profile.get("bio"),
            "blur": profile.get("blur", False)
        }
    except Exception as e:
        return {"photo": None, "bio": None, "blur": False}

# -----------------------------
# USER ROUTES
# -----------------------------

@app.post("/api/register")
async def register(data: dict, db: Session = Depends(get_db)):
    player_name = data.get("player_name", "").strip()
    if not player_name:
        raise HTTPException(400, "Name required")

    ticket = (
        db.query(Ticket)
        .filter(Ticket.is_assigned == False)
        .with_for_update(nowait=True)
        .first()
    )
    if not ticket:
        raise HTTPException(400, "Game full")

    ticket.is_assigned = True
    ticket.player_name = player_name
    ticket.assigned_at = datetime.now()
    db.commit()
    db.refresh(ticket)

    return {"ticket_id": str(ticket.id), "grid": ticket.grid, "player_name": ticket.player_name}


@app.get("/api/ticket/{ticket_id}")
async def get_ticket(ticket_id: str, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(404, "Ticket not found")

    picked_names = [n[0] for n in db.query(Name.name_text).filter(Name.is_picked == True).all()]

    return {
        "ticket_id": str(ticket.id),
        "player_name": ticket.player_name,
        "grid": ticket.grid,
        "status": ticket.status,
        "picked_names": picked_names
    }


@app.get("/api/game-status")
async def game_status(db: Session = Depends(get_db)):
    picked = db.query(Name).filter(Name.is_picked == True).order_by(Name.pick_order).all()

    picked_names = [
        {"name": n.name_text, "order": n.pick_order, "picked_at": str(n.picked_at)}
        for n in picked
    ]

    lock_state = db.query(GameState).filter(GameState.key == 'claim_lock').first()
    is_locked = lock_state.value == "true" if lock_state else False

    winners = db.query(Ticket).filter(Ticket.status == 'winner').all()
    winner_list = [{"name": t.player_name, "ticket_id": str(t.id)} for t in winners]

    last_pick = picked[-1] if picked else None

    return {
        "picked_names": picked_names,
        "is_locked": is_locked,
        "winners": winner_list,
        "last_pick_time": str(last_pick.picked_at) if last_pick else None
    }


@app.post("/api/claim")
async def claim(data: dict, db: Session = Depends(get_db)):
    ticket_id = data.get("ticket_id")

    lock = db.execute(text("SELECT pg_try_advisory_lock(1) AS got_lock")).fetchone()
    if not lock[0]:
        return {"success": False, "message": "Claim in progress"}

    try:
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket or ticket.status != 'active':
            return {"success": False, "message": "Invalid ticket"}

        # VALIDATE TICKET
        is_valid = validate_ticket(ticket, db)

        claim = ClaimQueue(ticket_id=ticket_id, is_valid=is_valid)  # ADD is_valid
        db.add(claim)

        ticket.status = 'claimed'
        ticket.claimed_at = datetime.now()

        lock_state = db.query(GameState).filter(GameState.key == 'claim_lock').first()
        if lock_state:
            lock_state.value = "true"
        else:
            db.add(GameState(key='claim_lock', value='true'))

        db.commit()

        position = db.query(ClaimQueue).filter(ClaimQueue.status == 'pending').count()
        return {"success": True, "queue_position": position}

    finally:
        db.execute(text("SELECT pg_advisory_unlock(1)"))
        
# -----------------------------
# ADMIN ROUTES
# -----------------------------

@app.post("/api/admin/login")
async def admin_login(data: dict):
    if data.get("password") != ADMIN_PASSWORD:
        raise HTTPException(401, "Invalid password")
    return {"success": True, "token": "admin_authenticated"}


@app.post("/api/admin/pick-name")
async def pick_name(authorization: str = Header(None), db: Session = Depends(get_db)):
    unpicked = db.query(Name).filter(Name.is_picked == False).all()
    if not unpicked:
        raise HTTPException(400, "No names left")

    selected = random.choice(unpicked)
    max_order = db.query(func.max(Name.pick_order)).scalar() or 0

    selected.is_picked = True
    selected.picked_at = datetime.now()
    selected.pick_order = max_order + 1

    db.commit()
    db.refresh(selected)

    remaining = db.query(Name).filter(Name.is_picked == False).count()

    return {
        "picked_name": selected.name_text,
        "remaining": remaining,
        "order": selected.pick_order
    }


@app.get("/api/admin/claims")
async def get_claims(authorization: str = Header(None), db: Session = Depends(get_db)):
    claims = db.query(ClaimQueue).filter(ClaimQueue.status == 'pending').order_by(ClaimQueue.claimed_at).all()

    result = []
    for claim in claims:
        ticket = db.query(Ticket).filter(Ticket.id == claim.ticket_id).first()
        picked_names = [n.name_text for n in db.query(Name).filter(Name.is_picked == True).all()]

        result.append({
            "claim_id": claim.id,
            "ticket_id": str(ticket.id),
            "player_name": ticket.player_name,
            "grid": ticket.grid,
            "picked_names": picked_names,
            "claimed_at": str(claim.claimed_at),
            "is_valid": claim.is_valid  # ADD THIS
        })

    return result


@app.post("/api/admin/verify-claim")
async def verify_claim(data: dict, authorization: str = Header(None), db: Session = Depends(get_db)):
    claim_id = data.get("claim_id")
    is_valid = data.get("is_valid")

    claim = db.query(ClaimQueue).filter(ClaimQueue.id == claim_id).first()
    if not claim:
        raise HTTPException(404, "Claim not found")

    ticket = db.query(Ticket).filter(Ticket.id == claim.ticket_id).first()

    if is_valid:
        claim.status = 'verified'
        claim.verified_at = datetime.now()
        ticket.status = 'winner'
    else:
        claim.status = 'rejected'
        claim.verified_at = datetime.now()
        ticket.status = 'active'

    pending = db.query(ClaimQueue).filter(ClaimQueue.status == 'pending').count()
    if pending == 0:
        lock_state = db.query(GameState).filter(GameState.key == 'claim_lock').first()
        if lock_state:
            lock_state.value = "false"

    db.commit()

    return {"success": True, "winner": is_valid}


@app.post("/api/admin/reset-game")
async def reset_game(authorization: str = Header(None), db: Session = Depends(get_db)):
    db.query(ClaimQueue).delete()
    db.query(Name).update({
        Name.is_picked: False,
        Name.picked_at: None,
        Name.pick_order: None
    })
    db.query(Ticket).update({
        Ticket.is_assigned: False,
        Ticket.status: 'active',
        Ticket.player_name: None
    })
    db.commit()
    return {"success": True}

@app.get("/api/admin/pending-claims")
async def pending_claims(db: Session = Depends(get_db)):
    pending = db.query(ClaimQueue).filter(ClaimQueue.status == 'pending').order_by(ClaimQueue.created_at).all()
    
    claims = []
    for claim in pending:
        ticket = db.query(Ticket).filter(Ticket.id == claim.ticket_id).first()
        claims.append({
            "claim_id": claim.id,
            "ticket_id": str(ticket.id),
            "player_name": ticket.player_name,
            "claimed_at": str(claim.created_at),
            "is_valid": claim.is_valid  # ADD THIS
        })
    
    return {"pending_claims": claims}

@app.get("/api/admin/qr-code")
async def get_qr_code():
    import qrcode, io, base64

    url = JOIN_URL

    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buf = io.BytesIO()
    img.save(buf, format='PNG')
    img_b64 = base64.b64encode(buf.getvalue()).decode()

    return {"qr_code": f"data:image/png;base64,{img_b64}", "url": url}

@app.post("/api/resolve-claim")
async def resolve_claim(data: dict, db: Session = Depends(get_db)):
    claim_id = data["claim_id"]
    approved = data["approved"]
    
    claim = db.query(ClaimQueue).get(claim_id)
    ticket = db.query(Ticket).filter(Ticket.id == claim.ticket_id).first()
    
    if approved:
        claim.status = 'approved'
        ticket.status = 'winner'
    else:
        claim.status = 'rejected'
        ticket.status = 'active'
    
    # UNLOCK
    lock_state = db.query(GameState).filter(GameState.key == 'claim_lock').first()
    lock_state.value = "false"
    
    db.commit()
    return {"success": True}

# -----------------------------
# STARTUP EVENT - Database Initialization
# -----------------------------

@app.on_event("startup")
async def startup_event():
    try:
        # CREATE TABLES
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created")
        
        with engine.connect() as conn:
            # ⭐ SEED NAMES TABLE FIRST
            names_count = conn.execute(text("SELECT COUNT(*) FROM names")).fetchone()[0]
            if names_count == 0:
                print("📝 Seeding names table...")
                BASE_DIR = os.path.dirname(os.path.abspath(__file__))
                NAMES_FILE = os.path.join(BASE_DIR, "names.json")
                
                if os.path.exists(NAMES_FILE):
                    with open(NAMES_FILE) as f:
                        names_list = json.load(f)
                    print(f"✅ Loaded {len(names_list)} names from names.json")
                else:
                    print("⚠️ names.json not found, using defaults")
                    names_list = [f"Player_{i}" for i in range(1, 91)]
                
                # Insert names into database
                for name in names_list:
                    conn.execute(
                        text("INSERT INTO names (name_text, is_picked, pick_order) VALUES (:name, false, NULL)"),
                        {"name": name}
                    )
                conn.commit()
                print(f"✅ Seeded {len(names_list)} names into database")
            else:
                print(f"✅ Found {names_count} names in database")
            
            # ⭐ THEN GENERATE TICKETS
            tickets_count = conn.execute(text("SELECT COUNT(*) FROM tickets")).fetchone()[0]
            if tickets_count == 0:
                print("🎫 Generating tickets...")
                
                # Get names from database
                result = conn.execute(text("SELECT name_text FROM names ORDER BY id"))
                db_names = [row[0] for row in result]
                
                if not db_names:
                    raise Exception("No names found in database!")
                
                generated = pre_generate_tickets(db_names, count=min(len(db_names), 100))
                
                for t in generated:
                    conn.execute(
                        Ticket.__table__.insert().values(
                            grid=t["grid"],
                            is_assigned=False,
                            status="active"
                        )
                    )
                conn.commit()
                print(f"✅ Generated {len(generated)} tickets")
            else:
                print(f"✅ Found {tickets_count} existing tickets")
            
            # ⭐ INITIALIZE GAME STATE
            game_state_count = conn.execute(text("SELECT COUNT(*) FROM game_state")).fetchone()[0]
            if game_state_count == 0:
                print("🎮 Initializing game state...")
                conn.execute(
                    text("INSERT INTO game_state (key, value) VALUES ('claim_lock', 'false')")
                )
                conn.commit()
                print("✅ Game state initialized")
            else:
                # RESET LOCK ON RESTART
                print("🔓 Resetting claim lock...")
                conn.execute(
                    text("UPDATE game_state SET value = 'false' WHERE key = 'claim_lock'")
                )
                conn.commit()
                print("✅ Claim lock reset to false")
                
    except Exception as e:
        print(f"❌ Startup error: {e}")
        import traceback
        traceback.print_exc()
# -----------------------------
# PRODUCTION ENTRYPOINT
# -----------------------------
def validate_ticket(ticket, db):
    """Check if all names on ticket are actually picked"""
    picked_names = {n.name_text for n in db.query(Name).filter(Name.is_picked == True).all()}
    
    ticket_names = [cell for row in ticket.grid for cell in row if cell]
    
    for name in ticket_names:
        if name not in picked_names:
            return False
    
    return True

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)