from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Table
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

# Association table for many-to-many relationship between providers and districts
provider_coverage = Table(
    'provider_coverage',
    Base.metadata,
    Column('provider_id', Integer, ForeignKey('bus_providers.id'), primary_key=True),
    Column('district_id', Integer, ForeignKey('districts.id'), primary_key=True)
)


class District(Base):
    __tablename__ = "districts"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    
    # Relationships
    dropping_points = relationship("DroppingPoint", back_populates="district", cascade="all, delete-orphan")
    providers = relationship("BusProvider", secondary=provider_coverage, back_populates="districts")


class DroppingPoint(Base):
    __tablename__ = "dropping_points"
    
    id = Column(Integer, primary_key=True, index=True)
    district_id = Column(Integer, ForeignKey("districts.id"), nullable=False)
    name = Column(String, nullable=False)
    price = Column(Integer, nullable=False)
    
    # Relationships
    district = relationship("District", back_populates="dropping_points")


class BusProvider(Base):
    __tablename__ = "bus_providers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    
    # Relationships
    districts = relationship("District", secondary=provider_coverage, back_populates="providers")
    bookings = relationship("Booking", back_populates="provider")


class Booking(Base):
    __tablename__ = "bookings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_name = Column(String, nullable=False)
    phone = Column(String, nullable=False, index=True)
    from_district = Column(String, nullable=False)
    to_district = Column(String, nullable=False)
    bus_provider_id = Column(Integer, ForeignKey("bus_providers.id"), nullable=False)
    travel_date = Column(String, nullable=False)
    booking_date = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="active")  # active, cancelled
    
    # Relationships
    provider = relationship("BusProvider", back_populates="bookings")