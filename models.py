from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Property(Base):
    __tablename__ = 'properties'
    
    account_number = Column(String(20), primary_key=True)
    street_address = Column(String)
    city = Column(String)
    zip_code = Column(String)
    neighborhood_code = Column(String)
    market_area = Column(String)
    market_description = Column(String)
    year_built = Column(Integer)
    building_area = Column(Float)
    land_area = Column(Float)
    acreage = Column(Float)
    land_value = Column(Float)
    building_value = Column(Float)
    extra_features_value = Column(Float)
    total_appraised_value = Column(Float)
    total_market_value = Column(Float)
    cdu = Column(Float)
    grade = Column(String)