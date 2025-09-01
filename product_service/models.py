from sqlalchemy import Column, Integer, String, Float
from db import Base
class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    price = Column(Float, nullable=False)
    currency = Column(String(8), nullable=False, default="USD")
    stock = Column(Integer, nullable=False, default=0)
