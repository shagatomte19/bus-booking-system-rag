from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from ..database import get_db
from ..models import Booking, BusProvider
from ..schemas import BookingCreate, BookingResponse

router = APIRouter(prefix="/api/bookings", tags=["bookings"])


@router.post("", response_model=BookingResponse)
def create_booking(
    booking_data: BookingCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new booking
    """
    # Validate bus provider exists
    provider = db.query(BusProvider).filter(
        BusProvider.name == booking_data.bus_provider
    ).first()
    
    if not provider:
        raise HTTPException(
            status_code=404,
            detail=f"Bus provider '{booking_data.bus_provider}' not found"
        )
    
    # Validate date format
    try:
        datetime.strptime(booking_data.travel_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid date format. Use YYYY-MM-DD"
        )
    
    # Create booking
    booking = Booking(
        user_name=booking_data.user_name,
        phone=booking_data.phone,
        from_district=booking_data.from_district,
        to_district=booking_data.to_district,
        bus_provider_id=provider.id,
        travel_date=booking_data.travel_date,
        status="active"
    )
    
    db.add(booking)
    db.commit()
    db.refresh(booking)
    
    # Create response with provider name
    response = BookingResponse(
        id=booking.id,
        user_name=booking.user_name,
        phone=booking.phone,
        from_district=booking.from_district,
        to_district=booking.to_district,
        bus_provider=provider.name,
        travel_date=booking.travel_date,
        booking_date=booking.booking_date,
        status=booking.status
    )
    
    return response


@router.get("/{phone}", response_model=List[BookingResponse])
def get_bookings_by_phone(
    phone: str,
    db: Session = Depends(get_db)
):
    """
    Get all bookings for a phone number
    """
    bookings = db.query(Booking).filter(Booking.phone == phone).all()
    
    # Build response with provider names
    responses = []
    for booking in bookings:
        provider = db.query(BusProvider).filter(
            BusProvider.id == booking.bus_provider_id
        ).first()
        
        responses.append(BookingResponse(
            id=booking.id,
            user_name=booking.user_name,
            phone=booking.phone,
            from_district=booking.from_district,
            to_district=booking.to_district,
            bus_provider=provider.name if provider else "Unknown",
            travel_date=booking.travel_date,
            booking_date=booking.booking_date,
            status=booking.status
        ))
    
    return responses


@router.delete("/{booking_id}")
def cancel_booking(
    booking_id: int,
    db: Session = Depends(get_db)
):
    """
    Cancel a booking
    """
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    if booking.status == "cancelled":
        raise HTTPException(status_code=400, detail="Booking already cancelled")
    
    booking.status = "cancelled"
    db.commit()
    
    return {"message": "Booking cancelled successfully", "booking_id": booking_id}