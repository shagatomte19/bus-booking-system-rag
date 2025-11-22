from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func  # Add this import
from typing import List
from ..database import get_db
from ..models import BusProvider, District, DroppingPoint, provider_coverage
from ..schemas import BusSearchRequest, BusSearchResult, BusProviderResponse

router = APIRouter(prefix="/api/buses", tags=["buses"])


@router.post("/search", response_model=List[BusSearchResult])
def search_buses(
    search_request: BusSearchRequest,
    db: Session = Depends(get_db)
):
    """
    Search for buses between two districts
    """
    from_district = search_request.from_district
    to_district = search_request.to_district
    max_price = search_request.max_price
    
    # Validate districts exist
    from_dist = db.query(District).filter(District.name == from_district).first()
    to_dist = db.query(District).filter(District.name == to_district).first()
    
    if not from_dist:
        raise HTTPException(status_code=404, detail=f"District '{from_district}' not found")
    if not to_dist:
        raise HTTPException(status_code=404, detail=f"District '{to_district}' not found")
    
    # Find providers that cover both districts
    query = db.query(BusProvider).join(
        provider_coverage, BusProvider.id == provider_coverage.c.provider_id
    ).filter(
        provider_coverage.c.district_id.in_([from_dist.id, to_dist.id])
    ).group_by(BusProvider.id).having(
        func.count(provider_coverage.c.district_id) == 2  # Changed from db.func.count
    )
    
    providers = query.all()
    
    if not providers:
        return []
    
    # Get dropping points for destination district
    dropping_points = db.query(DroppingPoint).filter(
        DroppingPoint.district_id == to_dist.id
    )
    
    if max_price:
        dropping_points = dropping_points.filter(DroppingPoint.price <= max_price)
    
    dropping_points = dropping_points.all()
    
    # Build results
    results = []
    for provider in providers:
        for dp in dropping_points:
            results.append(BusSearchResult(
                provider_name=provider.name,
                drop_point=dp.name,
                price=dp.price,
                from_district=from_district,
                to_district=to_district
            ))
    
    return results


@router.get("/providers", response_model=List[BusProviderResponse])
def get_all_providers(db: Session = Depends(get_db)):
    """
    Get all bus providers
    """
    providers = db.query(BusProvider).all()
    return providers