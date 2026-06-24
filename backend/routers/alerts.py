from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db, Alert

router = APIRouter()

@router.get("/alerts")
def get_alerts(db: Session = Depends(get_db)):
    alerts = db.query(Alert).order_by(Alert.created_at.desc()).all()
    return [
        {
            "id": a.id,
            "loan_id": a.loan_id,
            "alert_type": a.alert_type,
            "severity": a.severity,
            "message": a.message,
            "is_read": a.is_read,
            "created_at": a.created_at.isoformat() if isinstance(a.created_at, datetime) else a.created_at
        }
        for a in alerts
    ]

@router.patch("/alerts/{alert_id}/read")
def read_alert(alert_id: str, db: Session = Depends(get_db)):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
        
    alert.is_read = True
    db.commit()
    return {"status": "success", "message": "Alert marked as read"}
