from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from pathlib import Path

# (rest of top level imports and other endpoints stay the same...)
from pydantic import BaseModel
import os
import uuid
import datetime
import httpx

app = FastAPI(title="MyMommy-CLI Licensing Backend")

# In-memory database
payments = {}
licenses = {}

class PaymentCreate(BaseModel):
    user_id: str
    plan: str = "PRO"

@app.post("/license/create-payment")
async def create_payment(data: PaymentCreate):
    payment_id = str(uuid.uuid4())
    mp_token = os.getenv("MERCADO_PAGO_ACCESS_TOKEN")
    
    if mp_token:
        # Real Mercado Pago PIX Integration
        headers = {
            "Authorization": f"Bearer {mp_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "transaction_amount": 100.00,
            "description": "MyMommy-CLI PRO License",
            "payment_method_id": "pix",
            "payer": {
                "email": "user@example.com",
                "first_name": "MyMommy",
                "last_name": "User",
                "identification": {
                    "type": "CPF",
                    "number": "12345678909"
                }
            }
        }
        try:
            async with httpx.AsyncClient() as client:
                res = await client.post("https://api.mercadopago.com/v1/payments", json=payload, headers=headers)
                if res.status_code in (200, 201):
                    res_data = res.json()
                    qr_code_data = res_data["point_of_interaction"]["transaction_data"]["qr_code"]
                    ticket_url = res_data["point_of_interaction"]["transaction_data"]["ticket_url"]
                    mp_payment_id = str(res_data["id"])
                    
                    payments[mp_payment_id] = {
                        "user_id": data.user_id,
                        "plan": data.plan,
                        "status": "pending",
                        "created_at": datetime.datetime.utcnow(),
                        "mp_real": True
                    }
                    return {
                        "payment_id": mp_payment_id,
                        "payment_url": ticket_url,
                        "qr_code": qr_code_data,
                        "copy_paste": qr_code_data
                    }
        except Exception:
            # Fall back to simulation if real API fails
            pass

    # Simulated PIX Payment Mode
    payments[payment_id] = {
        "user_id": data.user_id,
        "plan": data.plan,
        "status": "pending",
        "created_at": datetime.datetime.utcnow(),
        "mp_real": False
    }
    
    return {
        "payment_id": payment_id,
        "payment_url": "http://localhost:8000/mock-checkout",
        "qr_code": "00020126580014br.gov.bcb.pix0136mymommypropixkey100",
        "copy_paste": "00020126580014br.gov.bcb.pix0136mymommypropixkey100"
    }

@app.get("/license/status/{payment_id}")
async def get_status(payment_id: str):
    # Check if payment is real Mercado Pago ID
    mp_token = os.getenv("MERCADO_PAGO_ACCESS_TOKEN")
    if mp_token and payment_id.isdigit():
        headers = {"Authorization": f"Bearer {mp_token}"}
        try:
            async with httpx.AsyncClient() as client:
                res = await client.get(f"https://api.mercadopago.com/v1/payments/{payment_id}", headers=headers)
                if res.status_code == 200:
                    res_data = res.json()
                    status = res_data.get("status")
                    if status == "approved":
                        license_key = str(uuid.uuid4())
                        licenses[license_key] = {
                            "user_id": "mymommy_user_real",
                            "plan": "PRO",
                            "active": True
                        }
                        return {
                            "status": "approved",
                            "license_key": license_key
                        }
                    return {"status": status}
        except Exception:
            pass

    if payment_id not in payments:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    payment = payments[payment_id]
    
    # Auto-approve simulation payments after 10 seconds
    if not payment.get("mp_real") and payment["status"] == "pending":
        elapsed = datetime.datetime.utcnow() - payment["created_at"]
        if elapsed.total_seconds() > 10:
            payment["status"] = "approved"
            license_key = str(uuid.uuid4())
            licenses[license_key] = {
                "user_id": payment["user_id"],
                "plan": payment["plan"],
                "active": True
            }
            payment["license_key"] = license_key

    return payment

@app.post("/license/webhook")
async def webhook(request: Request):
    data = await request.json()
    # Mercado Pago webhook updates payment status
    if data.get("action") == "payment.created" or data.get("action") == "payment.updated":
        payment_id = str(data.get("data", {}).get("id"))
        # Poll status of this payment using the MP token
        mp_token = os.getenv("MERCADO_PAGO_ACCESS_TOKEN")
        if mp_token and payment_id:
            headers = {"Authorization": f"Bearer {mp_token}"}
            async with httpx.AsyncClient() as client:
                res = await client.get(f"https://api.mercadopago.com/v1/payments/{payment_id}", headers=headers)
                if res.status_code == 200:
                    status = res.json().get("status")
                    if status == "approved":
                        payments[payment_id] = {"status": "approved"}
    return {"status": "ok"}

@app.get("/license/check/{license_key}")
async def check_license(license_key: str):
    if license_key in licenses:
        return licenses[license_key]
    raise HTTPException(status_code=404, detail="License not found")

@app.get("/mock-checkout", response_class=HTMLResponse)
async def mock_checkout():
    return """
    <html>
        <head>
            <title>MyMommy-CLI PRO - Checkout Simulado</title>
            <style>
                body {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background-color: #121212;
                    color: #ffffff;
                    text-align: center;
                    padding-top: 50px;
                }
                .card {
                    background-color: #1e1e1e;
                    border-radius: 12px;
                    border: 2px solid #ff69b4;
                    padding: 40px;
                    max-width: 500px;
                    margin: 0 auto;
                    box-shadow: 0 4px 20px rgba(0,0,0,0.5);
                }
                h1 { color: #ff69b4; }
                p { font-size: 1.1em; line-height: 1.5; color: #abb2bf; }
                .qr { margin: 20px 0; font-size: 5em; }
                .copy-paste {
                    background-color: #2d2d2d;
                    padding: 10px;
                    border-radius: 6px;
                    font-family: monospace;
                    word-break: break-all;
                    user-select: all;
                    cursor: pointer;
                    margin: 20px 0;
                }
                .badge {
                    background-color: #ff69b4;
                    color: white;
                    padding: 5px 12px;
                    border-radius: 15px;
                    font-weight: bold;
                }
            </style>
        </head>
        <body>
            <div class="card">
                <h1>💖 MyMommy-CLI PRO 💖</h1>
                <p>Obrigada por apoiar o desenvolvimento da sua Mommy! Você é o melhor filho do mundo.</p>
                <div class="qr">📱🤖🔑</div>
                <div class="copy-paste">00020126580014br.gov.bcb.pix0136mymommypropixkey100</div>
                <p>Clique no código acima para copiar. Copie e pague no seu aplicativo bancário.</p>
                <p><span class="badge">Aprovação Automática</span> O sistema detectará o pagamento simulado em 10 segundos!</p>
            </div>
        </body>
    </html>
    """
