
import sys
import traceback
from sqlalchemy import create_engine, text
import sqlalchemy
from sqlalchemy.exc import OperationalError, NoResultFound
from sqlalchemy.orm import Session
from sqlalchemy import insert
from sqlalchemy import func

from typing import Optional, TypeVar

import time
from datetime import datetime

from src.models.models import Base

A = TypeVar("A", bound=Base)


CONNECTION_URI = "sqlite:///db/Preciosv2.sqlite"


class DataBase():
    """Genera un objeto de la base de datos
    """

    def __init__(self, model: A) -> None:
        self.engine = create_engine(CONNECTION_URI, echo=False)
        self.model = model

    def init_database_ara(self):

        query = f"""
            CREATE TABLE IF NOT EXISTS {self.name_data_base} (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                Categoria text,
                Sub_categoria text,
                Nombre text,
                Cantidad INTEGER,
                Unidad text,
                Precio REAL,
                Fecha_de_lectura TEXT,
                Hora_de_lectura TEXT,
                UNIQUE(Nombre,Categoria,Cantidad,Fecha_de_lectura) ON CONFLICT IGNORE
            );
            """
        self.engine.execute(query)

    def init_database_olimpica(self):

        query = f"""
            CREATE TABLE IF NOT EXISTS {self.name_data_base} (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                Departamento text,
                Categoria text,
                Sub_categoria text,
                Nombre_producto text,
                Precio_oferta REAL,
                Cantidad REAL,
                Unidad text,
                Precio_normal REAL,
                Fecha_resultados TEXT,
                Hora_resultados TEXT,
                UNIQUE(Nombre_producto,Categoria,Fecha_resultados) ON CONFLICT IGNORE
            );
            """
        self.engine.execute(query)

    def dataframe_to_sql(self, data):
        while True:
            try:
                data.to_sql(self.name_data_base, self.engine,
                            if_exists='append', index=False)
                break
            except OperationalError:
                print("Por favor guarde cambios en la base de datos")
                time.sleep(5)
                continue

    @classmethod
    def save_data(cls, engine, model, data: list | dict):
        try:
            with Session(engine) as session:
                session.execute(
                    insert(model)
                    .prefix_with("OR IGNORE")
                    .values(data),

                )
                session.commit()
        except sqlalchemy.exc.OperationalError as e:
            # traceback.print_exception(**sys.exc_info())
            print(e)
            middle = int(len(data)/2)
            first = data[0:middle]
            second = data[middle:]
            DataBase.save_data(engine, model, first)
            DataBase.save_data(engine, model, second)

    def consulta_sql(self, columns: None = None, filters=None):
        with Session(self.engine) as session:
            if columns and filters:
                return session.query(*columns).filter(*filters).all()
            elif columns and not filters:
                return session.query(*columns).all()
            elif not columns and filters:
                return session.query(self.model).filter(*filters).all()
            elif not columns and not filters:
                return session.query(self.model).all()

    def consulta_sql_unica(self, columns: None = None, filters=None):
        with Session(self.engine) as session:
            try:
                if columns and filters:
                    return session.query(*columns).filter(*filters).one()
                elif columns and not filters:
                    return session.query(*columns).one()
                elif not columns and filters:
                    return session.query(self.model).filter(*filters).one()
                elif not columns and not filters:
                    return session.query(self.model).one()
            except NoResultFound:
                return None

    def consulta_sql_query_one(self, query):
        with self.engine.connect() as conn:
            return conn.execute(text(query)).fetchone()._asdict()

    def last_item_db(self, date: datetime = None):
        # date = datetime(2023,9,2).strftime("%Y-%m-%d")
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        else:
            date = date.strftime("%Y-%m-%d")
        category = subcategory = False
        for col in self.model.__table__.columns.keys():
            if col == 'categoria':
                category = True
            if col == 'sub_categoria':
                subcategory = True
        columns = []
        if category:
            columns.append(self.model.categoria.label("categoria"))
        if subcategory:
            columns.append(self.model.sub_categoria.label("sub_categoria"))
        max_id = self.consulta_sql_unica([func.max(self.model.id)])
        filters = [self.model.fecha_resultados ==
                   date, self.model.id == max_id[0]]

        res = self.consulta_sql_unica(columns, filters)
        if res:
            res = res._asdict()
        return res

    def close(self):
        self.engine.dispose()
