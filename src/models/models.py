from typing import List
from typing import Optional
from sqlalchemy import ForeignKey
from sqlalchemy import String, Float, Date, UniqueConstraint, Time
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from datetime import datetime


class Base(DeclarativeBase):
    pass


class Exito(Base):
    __tablename__ = "exito"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nombre_producto: Mapped[str] = mapped_column(String(200))
    categoria: Mapped[str] = mapped_column(String(50))
    sub_categoria: Mapped[str] = mapped_column(String(50))
    precio_bajo: Mapped[float]
    precio_alto: Mapped[float]
    cantidad: Mapped[int]
    unidad: Mapped[str] = mapped_column(String(10))
    fecha_resultados = mapped_column(Date, default=datetime.now().date())
    hora_resultados = mapped_column(Time, default=datetime.now().time())

    __table_args__ = (UniqueConstraint('categoria', 'nombre_producto',
                      'fecha_resultados', name='_product_uc'),)

    def __repr__(self) -> str:
        return f"Exito(id={self.id!r}, Nombre_producto={self.Nombre_producto!r}, Precio_alto={self.Precio_alto!r})"
