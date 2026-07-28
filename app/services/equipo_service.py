from datetime import datetime
from typing import Optional

from sqlmodel import Session, select

from app.models import Equipo
from app.schemas.equipo import EquipoCreate, EquipoUpdate


class EquipoService:

    @staticmethod
    def listar(
        session: Session,
        q: Optional[str] = None,
        empresa_id: Optional[int] = None,
        area: Optional[str] = None,
        estado: Optional[str] = None,
    ):

        statement = select(Equipo)

        if empresa_id is not None:
            statement = statement.where(Equipo.empresa_id == empresa_id)

        if area:
            statement = statement.where(Equipo.area == area)

        if estado:
            statement = statement.where(Equipo.estado_equipo == estado)

        equipos = session.exec(statement).all()

        if q:
            texto = q.lower()

            equipos = [
                e for e in equipos
                if texto in (e.codigo or "").lower()
                or texto in (e.nombre_equipo or "").lower()
                or texto in (e.serial or "").lower()
                or texto in (e.usuario_asignado or "").lower()
                or texto in (e.area or "").lower()
                or texto in (e.marca or "").lower()
            ]

        return equipos

    @staticmethod
    def obtener(
        session: Session,
        equipo_id: int,
    ):

        return session.get(Equipo, equipo_id)

    @staticmethod
    def obtener_por_codigo(
        session: Session,
        codigo: str,
    ):

        statement = select(Equipo).where(
            Equipo.codigo == codigo
        )

        return session.exec(statement).first()

    @staticmethod
    def crear(
        session: Session,
        datos: EquipoCreate,
    ) -> Equipo:

        existente = EquipoService.obtener_por_codigo(
            session,
            datos.codigo,
        )

        if existente:
            raise ValueError(
                f"Ya existe un equipo con el código '{datos.codigo}'."
            )

        equipo = Equipo(
            **datos.model_dump()
        )

        equipo.fecha_creacion = datetime.utcnow()
        equipo.fecha_actualizacion = datetime.utcnow()

        session.add(equipo)
        session.commit()
        session.refresh(equipo)

        return equipo

    @staticmethod
    def actualizar(
        session: Session,
        equipo: Equipo,
        datos: EquipoUpdate,
    ) -> Equipo:

        cambios = datos.model_dump(
            exclude_unset=True
        )

        if (
            "codigo" in cambios
            and cambios["codigo"] != equipo.codigo
        ):

            existente = EquipoService.obtener_por_codigo(
                session,
                cambios["codigo"],
            )

            if existente:
                raise ValueError(
                    f"Ya existe un equipo con el código '{cambios['codigo']}'."
                )

        for campo, valor in cambios.items():
            setattr(
                equipo,
                campo,
                valor,
            )

        equipo.fecha_actualizacion = datetime.utcnow()

        session.add(equipo)
        session.commit()
        session.refresh(equipo)

        return equipo

    @staticmethod
    def eliminar(
        session: Session,
        equipo: Equipo,
    ):

        session.delete(equipo)
        session.commit()