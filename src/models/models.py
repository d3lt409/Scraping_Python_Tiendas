from typing import List
from typing import Optional
from sqlalchemy import ForeignKey
from sqlalchemy import String, Float, Date, UniqueConstraint, Time
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
# from sqlalchemy.orm import relationship
from datetime import datetime


class Base(DeclarativeBase):
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nombre_producto: Mapped[str] = mapped_column(String(200))
    categoria: Mapped[str] = mapped_column(String(50))
    sub_categoria: Mapped[str] = mapped_column(String(50))

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Exito(Base):
    __tablename__ = "exito"
    precio_bajo: Mapped[float]
    precio_alto: Mapped[float]
    cantidad: Mapped[int]
    unidad: Mapped[str] = mapped_column(String(10))
    fecha_resultados = mapped_column(Date, default=datetime.now().date())
    hora_resultados = mapped_column(Time, default=datetime.now().time())

    __table_args__ = (UniqueConstraint('nombre_producto',
                      'fecha_resultados', name='_product_uc'),)

    def __repr__(self) -> str:
        return f"Exito(id={self.id!r}, Nombre_producto={self.nombre_producto!r}, Precio_alto={self.precio_alto!r})"


class D1(Base):
    __tablename__ = "d1"
    precio: Mapped[float]
    precio_unidad: Mapped[float]
    cantidad: Mapped[int]
    unidad: Mapped[str] = mapped_column(String(10))
    fecha_resultados = mapped_column(Date, default=datetime.now().date())
    hora_resultados = mapped_column(Time, default=datetime.now().time())

    __table_args__ = (UniqueConstraint('nombre_producto',
                      'fecha_resultados', name='_product_uc'),)

    def __repr__(self) -> str:
        return f"D1(id={self.id!r}, Nombre_producto={self.nombre_producto!r}, Precio={self.precio!r})"
    

class Olimpica(Base):
    __tablename__ = "olimpica"
    precio_bajo: Mapped[float]
    precio_alto: Mapped[float]
    cantidad: Mapped[int]
    unidad: Mapped[str] = mapped_column(String(10))
    fecha_resultados = mapped_column(Date, default=datetime.now().date())
    hora_resultados = mapped_column(Time, default=datetime.now().time())

    __table_args__ = (UniqueConstraint('nombre_producto',
                      'fecha_resultados', name='olim_product_uc'),)

    def __repr__(self) -> str:
        return f"Olimpica(id={self.id!r}, Nombre_producto={self.nombre_producto!r}, Precio_alto={self.precio_alto!r})"