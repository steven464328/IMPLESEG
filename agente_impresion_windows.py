import json
import sys
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HOST = "127.0.0.1"
PORT = 8765


def get_win32print():
    try:
        import win32print
        return win32print
    except ImportError:
        print("ERROR: pywin32 no está instalado.")
        print("Ejecute: python -m pip install pywin32")
        sys.exit(1)


win32print = get_win32print()


def listar_impresoras():
    impresoras = []
    for printer in win32print.EnumPrinters(2):
        # ENUMPRINTERS(2) devuelve el nombre en la posición 2.
        nombre = printer[2]
        if nombre and nombre not in impresoras:
            impresoras.append(nombre)
    return impresoras


def imprimir_zpl(nombre_impresora: str, zpl: str) -> int:
    if not nombre_impresora:
        raise ValueError("Debe indicar la impresora.")

    if not zpl:
        raise ValueError("El ZPL está vacío.")

    impresoras = listar_impresoras()
    if nombre_impresora not in impresoras:
        raise ValueError(
            f"La impresora '{nombre_impresora}' no está instalada/disponible "
            "en este PC."
        )

    handle = win32print.OpenPrinter(nombre_impresora)

    try:
        job_id = win32print.StartDocPrinter(
            handle,
            1,
            ("IMPULSEG - Etiquetas", None, "RAW"),
        )

        try:
            win32print.StartPagePrinter(handle)

            try:
                datos = zpl.encode("ascii")
                escritos = win32print.WritePrinter(handle, datos)

                if escritos != len(datos):
                    raise RuntimeError(
                        f"Windows escribió {escritos} bytes de {len(datos)}."
                    )

            finally:
                win32print.EndPagePrinter(handle)

        finally:
            win32print.EndDocPrinter(handle)

        return job_id

    finally:
        win32print.ClosePrinter(handle)


class AgenteHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{hora}] {self.address_string()} - {fmt % args}")

    def send_json(self, payload, status=200):
        body = json.dumps(
            payload,
            ensure_ascii=False,
        ).encode("utf-8")

        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))

        # El agente escucha solamente en 127.0.0.1.
        # Cualquier página del ERP podrá consultarlo desde el navegador.
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header(
            "Access-Control-Allow-Methods",
            "GET, POST, OPTIONS",
        )
        self.send_header(
            "Access-Control-Allow-Headers",
            "Content-Type",
        )
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header(
            "Access-Control-Allow-Methods",
            "GET, POST, OPTIONS",
        )
        self.send_header(
            "Access-Control-Allow-Headers",
            "Content-Type",
        )
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self):
        try:
            if self.path == "/health":
                self.send_json(
                    {
                        "status": "ok",
                        "agente": "IMPLESEG Printer Agent",
                        "host": HOST,
                        "puerto": PORT,
                    }
                )
                return

            if self.path == "/printers":
                impresoras = listar_impresoras()

                self.send_json(
                    {
                        "status": "ok",
                        "impresoras": impresoras,
                        "cantidad": len(impresoras),
                    }
                )
                return

            self.send_json(
                {
                    "status": "error",
                    "detail": "Ruta no encontrada.",
                },
                404,
            )

        except Exception as exc:
            self.send_json(
                {
                    "status": "error",
                    "detail": str(exc),
                },
                500,
            )

    def do_POST(self):
        if self.path != "/print":
            self.send_json(
                {
                    "status": "error",
                    "detail": "Ruta no encontrada.",
                },
                404,
            )
            return

        try:
            content_length = int(
                self.headers.get("Content-Length", "0")
            )

            if content_length <= 0:
                raise ValueError("El cuerpo de la solicitud está vacío.")

            raw_body = self.rfile.read(content_length)
            data = json.loads(raw_body.decode("utf-8"))

            nombre_impresora = str(
                data.get("printer", "")
            ).strip()

            zpl = str(
                data.get("zpl", "")
            )

            job_id = imprimir_zpl(
                nombre_impresora,
                zpl,
            )

            self.send_json(
                {
                    "status": "ok",
                    "mensaje": "Trabajo enviado a la impresora.",
                    "impresora": nombre_impresora,
                    "job_id": job_id,
                    "bytes": len(zpl.encode("ascii")),
                }
            )

        except UnicodeEncodeError:
            self.send_json(
                {
                    "status": "error",
                    "detail": (
                        "El ZPL contiene caracteres que no son ASCII. "
                        "El agente espera ZPL compatible con la Zebra."
                    ),
                },
                400,
            )

        except Exception as exc:
            self.send_json(
                {
                    "status": "error",
                    "detail": str(exc),
                },
                500,
            )


def main():
    impresoras = listar_impresoras()

    print("=" * 60)
    print("IMPLESEG - AGENTE DE IMPRESIÓN WINDOWS")
    print("=" * 60)
    print(f"Escuchando únicamente en: http://{HOST}:{PORT}")
    print(f"Impresoras detectadas: {len(impresoras)}")

    for nombre in impresoras:
        print(f"  - {nombre}")

    print()
    print("Endpoints:")
    print(f"  GET  http://{HOST}:{PORT}/health")
    print(f"  GET  http://{HOST}:{PORT}/printers")
    print(f"  POST http://{HOST}:{PORT}/print")
    print()
    print("Deje esta ventana abierta mientras realiza la prueba.")
    print("Ctrl+C para detener el agente.")
    print("=" * 60)

    servidor = ThreadingHTTPServer(
        (HOST, PORT),
        AgenteHandler,
    )

    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nAgente detenido.")
    finally:
        servidor.server_close()


if __name__ == "__main__":
    main()
