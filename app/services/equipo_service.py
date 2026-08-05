from datetime import datetime
from typing import Optional

from sqlmodel import Session, select

from app.models import Equipo
from app.schemas.equipo import EquipoCreate, EquipoUpdate


class EquipoService:

    # ==========================================================
    # CONSULTAS
    # ==========================================================

    @staticmethod
    def listar(
        session: Session,
        q: Optional[str] = None,
        empresa: Optional[str] = None,
        tipo_equipo: Optional[str] = None,
        area: Optional[str] = None,
        estado: Optional[str] = None,
    ):

        statement = select(Equipo)

        if empresa:
            statement = statement.where(
                Equipo.empresa == empresa
            )

        if tipo_equipo:
            statement = statement.where(
                Equipo.tipo_equipo == tipo_equipo
            )

        if area:
            statement = statement.where(
                Equipo.area == area
            )

        if estado:
            statement = statement.where(
                Equipo.estado_equipo == estado
            )

        equipos = session.exec(statement).all()

        if not q:
            return equipos

        texto = q.lower()

        return [

            e

            for e in equipos

            if texto in (e.codigo or "").lower()
            or texto in (e.equipo or "").lower()
            or texto in (e.nombre_equipo or "").lower()
            or texto in (e.serial or "").lower()
            or texto in (e.usuario_asignado or "").lower()
            or texto in (e.area or "").lower()
            or texto in (e.marca or "").lower()
            or texto in (e.modelo_equipo or "").lower()
            or texto in (e.ip or "").lower()

        ]


    @staticmethod
    def obtener(
        session: Session,
        equipo_id: int,
    ):

        return session.get(
            Equipo,
            equipo_id,
        )


    @staticmethod
    def obtener_por_codigo(
        session: Session,
        codigo: str,
    ):

        return session.exec(

            select(Equipo).where(
                Equipo.codigo == codigo
            )

        ).first()


    # ==========================================================
    # CRUD
    # ==========================================================

    @staticmethod
    def crear(
        session: Session,
        datos: EquipoCreate,
    ) -> Equipo:

        if datos.codigo:

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

        ahora = datetime.utcnow()

        equipo.creado_en = ahora
        equipo.actualizado_en = ahora

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

        if "codigo" in cambios:

            if cambios["codigo"] != equipo.codigo:

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

        equipo.actualizado_en = datetime.utcnow()

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


    # ==========================================================
    # DASHBOARD
    # ==========================================================

    @staticmethod
    def total_equipos(session: Session):

        return session.exec(
            select(Equipo)
        ).count()


    @staticmethod
    def equipos_activos(session: Session):

        return len(

            session.exec(

                select(Equipo).where(
                    Equipo.estado_equipo == "ACTIVO"
                )

            ).all()

        )


    @staticmethod
    def equipos_por_empresa(
        session: Session,
        empresa: str,
    ):

        return session.exec(

            select(Equipo).where(
                Equipo.empresa == empresa
            )

        ).all()


    @staticmethod
    def equipos_por_usuario(
        session: Session,
        usuario: str,
    ):

        return session.exec(

            select(Equipo).where(
                Equipo.usuario_asignado == usuario
            )

        ).all()


    @staticmethod
    def equipos_por_area(
        session: Session,
        area: str,
    ):

        return session.exec(

            select(Equipo).where(
                Equipo.area == area
            )

        ).all()


    @staticmethod
    def equipos_sin_mantenimiento(
        session: Session,
    ):

        return session.exec(

            select(Equipo).where(
                Equipo.fecha_ultimo_mantenimiento == None
            )

        ).all()


    # ==========================================================
    # BUSCADOR GENERAL
    # ==========================================================

    @staticmethod
    def buscar(
        session: Session,
        texto: str,
    ):

        texto = texto.lower()

        equipos = session.exec(
            select(Equipo)
        ).all()

        return [

            e

            for e in equipos

            if texto in (e.codigo or "").lower()
            or texto in (e.equipo or "").lower()
            or texto in (e.nombre_equipo or "").lower()
            or texto in (e.serial or "").lower()
            or texto in (e.usuario_asignado or "").lower()
            or texto in (e.area or "").lower()
            or texto in (e.marca or "").lower()
            or texto in (e.modelo_equipo or "").lower()
            or texto in (e.ip or "").lower()
            or texto in (e.mac or "").lower()

        ]


    # ==========================================================
    # INDICADORES
    # ==========================================================

    @staticmethod
    def total_por_estado(
        session: Session,
        estado: str,
    ):

        return len(

            session.exec(

                select(Equipo).where(
                    Equipo.estado_equipo == estado
                )

            ).all()

        )


    @staticmethod
    def total_por_tipo(
        session: Session,
        tipo: str,
    ):

        return len(

            session.exec(

                select(Equipo).where(
                    Equipo.tipo_equipo == tipo
                )

            ).all()

        )


    @staticmethod
    def total_por_empresa(
        session: Session,
        empresa: str,
    ):

        return len(

            session.exec(

                select(Equipo).where(
                    Equipo.empresa == empresa
                )

            ).all()

        ) 