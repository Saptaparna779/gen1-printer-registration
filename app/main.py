"""
FastAPI app for the GEN 1 Printer Onboarding & Registration demo service.
Run with:
    uvicorn app.main:app --reload --port 8000
Docs available at http://localhost:8000/docs
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app import registration
from app.registration import RegistrationError, InvalidClaimCodeError
from app.auth import create_access_token, verify_token
from fastapi import Depends

app = FastAPI(title="GEN 1 Printer Onboarding & Registration (Demo)")


@app.get("/health")
def health_check():
    """Liveness check -- confirms the application is running and reachable."""
    return {"status": "ok"}


class TokenRequest(BaseModel):
    user_id: str


@app.post("/auth/token")
def issue_token(req: TokenRequest):
    """
    Demo token issuance endpoint. In a real system this would verify a
    password or other credential first -- for this demo, any user_id is
    accepted and issued a signed token.
    """
    token = create_access_token(subject=req.user_id)
    return {"access_token": token, "token_type": "bearer"}


class RegisterRequest(BaseModel):
    serial_number: str
    model_number: str
    firmware_version: str
    simulate_welcome_page_failure: bool = False


class ClaimRequest(BaseModel):
    claim_code: str
    user_id: str


@app.post("/printers/register")
def register_printer(req: RegisterRequest, user_id: str = Depends(verify_token)):
    try:
        printer = registration.register_printer(
            serial_number=req.serial_number,
            model_number=req.model_number,
            firmware_version=req.firmware_version,
            simulate_welcome_page_failure=req.simulate_welcome_page_failure,
        )
    except RegistrationError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return {
        "printer_id": printer.printer_id,
        "cloud_id": printer.cloud_id,
        "printer_email_id": printer.printer_email_id,
        "claim_code": printer.claim_code.code,
        "claim_code_expires_at": printer.claim_code.expires_at.isoformat(),
        "xmpp_node": printer.xmpp_node,
        "status": printer.status,
        "history": printer.registration_history,
    }


@app.post("/printers/claim")
def claim_printer(req: ClaimRequest):
    try:
        printer = registration.claim_printer(req.claim_code, req.user_id)
    except InvalidClaimCodeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {
        "printer_id": printer.printer_id,
        "status": printer.status,
        "owner_user_id": printer.owner_user_id,
    }


@app.get("/printers/{printer_id}")
def get_printer(printer_id: str):
    from app import store
    printer = store.get_printer(printer_id)
    if printer is None:
        raise HTTPException(status_code=404, detail="Printer not found")
    return {
        "printer_id": printer.printer_id,
        "serial_number": printer.serial_number,
        "cloud_id": printer.cloud_id,
        "printer_email_id": printer.printer_email_id,
        "status": printer.status,
        "owner_user_id": printer.owner_user_id,
        "xmpp_node": printer.xmpp_node,
        "history": printer.registration_history,
    }


@app.delete("/printers/{printer_id}")
def deregister_printer(printer_id: str):
    try:
        registration.deregister_printer(printer_id)
    except RegistrationError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return {"status": "DEREGISTERED", "printer_id": printer_id}

