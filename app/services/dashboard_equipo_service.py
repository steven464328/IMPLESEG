from datetime import datetime

from sqlmodel import Session, select

from app.models import Equipo


class DashboardEquipoService:

    @staticmethod
    def resumen(session: Session):

        equipos = session.exec(
            select(Equipo)
        ).all()

        hoy = datetime.now()

        total = len(equipos)

        activos = 0
        reparacion = 0
        baja = 0

        mantenimiento_vencido = 0
        mantenimiento_proximo = 0

        antivirus_vencido = 0

        sin_usuario = 0
        sin_serial = 0

        ram_baja = 0
        disco_antiguo = 0

        windows_antiguo = 0

        for e in equipos:

            estado = (e.estado_equipo or "").upper()

            if estado == "ACTIVO":
                activos += 1

            elif estado == "REPARACION":
                reparacion += 1

            elif estado == "BAJA":
                baja += 1

            if e.proximo_mantenimiento:

                if e.proximo_mantenimiento.date() < hoy.date():
                    mantenimiento_vencido += 1

                elif (e.proximo_mantenimiento - hoy).days <= 30:
                    mantenimiento_proximo += 1

            if e.licencia_antivirus:

                try:

                    fecha = datetime.fromisoformat(
                        str(e.licencia_antivirus)
                    )

                    if fecha.date() < hoy.date():
                        antivirus_vencido += 1

                except Exception:
                    pass

            if not e.usuario_asignado:
                sin_usuario += 1

            if not e.serial:
                sin_serial += 1

            if e.memoria_ram:

                txt = e.memoria_ram.upper()

                if "4" in txt or "2" in txt:
                    ram_baja += 1

            if e.disco_duro:

                txt = e.disco_duro.upper()

                if "HDD" in txt:
                    disco_antiguo += 1

            if e.version_so:

                txt = e.version_so.upper()

                if (
                    "WINDOWS 7" in txt
                    or "WINDOWS 8" in txt
                    or "WINDOWS XP" in txt
                ):
                    windows_antiguo += 1

        return {

            "total": total,

            "activos": activos,

            "reparacion": reparacion,

            "baja": baja,

            "mantenimiento_vencido": mantenimiento_vencido,

            "mantenimiento_proximo": mantenimiento_proximo,

            "antivirus_vencido": antivirus_vencido,

            "ram_baja": ram_baja,

            "disco_antiguo": disco_antiguo,

            "windows_antiguo": windows_antiguo,

            "sin_usuario": sin_usuario,

            "sin_serial": sin_serial,

        }