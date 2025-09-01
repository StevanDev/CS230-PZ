from sqlalchemy import Column, Integer, String
from db import Base
class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    user_id = Column(Integer, nullable=True)
    status = Column(String(32), nullable=False, default="CREATED")
