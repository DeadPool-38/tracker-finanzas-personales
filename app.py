import logging
from datetime import date

import pandas as pd
import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError
from supabase import Client, create_client
from supabase_auth.errors import AuthError

from cartera import Cartera
from repositorio_supabase import RepositorioSupabase
from transaccion import Transaccion


logger = logging.getLogger(__name__)

st.set_page_config(layout="wide")

categorias = [
    "Alimentación",
    "Transporte",
    "Entretenimiento",
    "Salud",
    "Educación",
    "Otros",
]


def crear_cliente_supabase() -> Client:
    try:
        configuracion = st.secrets["supabase"]
        url = configuracion["url"]
        clave = configuracion["anon_key"]
    except (KeyError, StreamlitSecretNotFoundError):
        st.error(
            "Falta configurar Supabase. Sigue las instrucciones de "
            "SUPABASE_SETUP.md para añadir la URL y la clave pública."
        )
        st.stop()

    return create_client(url, clave)


def mostrar_titulos():
    st.markdown(
        "<h1 style='color: #5CCB5F;'>Tracker de Finanzas Personales</h1>",
        unsafe_allow_html=True,
    )
    st.write(
        "Bienvenido a tu aplicación para el seguimiento de tus finanzas personales,  \n"
        "aquí puedes registrar tus ingresos y gastos,  así como visualizar tus finanzas "
        "de manera clara y sencilla."
    )
    st.caption("Versión 1.6 - Desarrollado por Ing. Alan Ocaña.")


def iniciar_sesion(cliente: Client):
    st.subheader("Accede a tus finanzas")
    tab_login, tab_registro = st.tabs(["Iniciar sesión", "Crear cuenta"])

    with tab_login:
        with st.form("formulario_login"):
            correo = st.text_input("Correo electrónico", key="correo_login")
            contrasena = st.text_input(
                "Contraseña", type="password", key="contrasena_login"
            )
            enviado = st.form_submit_button("Iniciar sesión")

        if enviado:
            if not correo.strip() or not contrasena:
                st.error("Escribe tu correo y contraseña.")
            else:
                try:
                    respuesta = cliente.auth.sign_in_with_password(
                        {"email": correo.strip(), "password": contrasena}
                    )
                except AuthError:
                    logger.exception("No se pudo iniciar sesión en Supabase.")
                    st.error("No se pudo iniciar sesión. Revisa tus datos e inténtalo.")
                else:
                    st.session_state.user_id = respuesta.user.id
                    st.session_state.user_email = respuesta.user.email
                    st.rerun()

    with tab_registro:
        with st.form("formulario_registro"):
            correo = st.text_input("Correo electrónico", key="correo_registro")
            contrasena = st.text_input(
                "Contraseña (mínimo 8 caracteres)",
                type="password",
                key="contrasena_registro",
            )
            confirmacion = st.text_input(
                "Confirma la contraseña",
                type="password",
                key="confirmacion_registro",
            )
            enviado = st.form_submit_button("Crear cuenta")

        if enviado:
            if not correo.strip() or len(contrasena) < 8:
                st.error("Escribe un correo y una contraseña de al menos 8 caracteres.")
            elif contrasena != confirmacion:
                st.error("Las contraseñas no coinciden.")
            else:
                try:
                    respuesta = cliente.auth.sign_up(
                        {"email": correo.strip(), "password": contrasena}
                    )
                except AuthError as error:
                    logger.exception("No se pudo crear la cuenta en Supabase.")
                    st.error(
                        f"No se pudo crear la cuenta: {error}"
                    )
                else:
                    if respuesta.session is None:
                        st.success(
                            "Cuenta creada. Confirma tu correo y luego inicia sesión."
                        )
                    else:
                        st.session_state.user_id = respuesta.user.id
                        st.session_state.user_email = respuesta.user.email
                        st.rerun()


def mostrar_cerrar_sesion(cliente: Client):
    st.sidebar.caption(f"Sesión: {st.session_state.user_email}")
    if st.sidebar.button("Cerrar sesión"):
        cliente.auth.sign_out()
        for clave in ("user_id", "user_email", "cartera", "cartera_user_id"):
            st.session_state.pop(clave, None)
        st.rerun()


def inicializar_cartera(repositorio: RepositorioSupabase, user_id: str):
    if (
        "cartera" not in st.session_state
        or st.session_state.get("cartera_user_id") != user_id
    ):
        transacciones = repositorio.cargar_transacciones(user_id)
        st.session_state.cartera = Cartera(transacciones)
        st.session_state.cartera_user_id = user_id


def importar_csv(repositorio: RepositorioSupabase, user_id: str):
    with st.expander("Importar desde CSV"):
        archivo = st.file_uploader("Selecciona un archivo CSV:", type=["csv"])
        if st.button("Importar transacciones"):
            if archivo is None:
                st.warning("Primero sube un archivo CSV.")
                return

            try:
                archivo.seek(0)
                df = pd.read_csv(archivo)
            except (pd.errors.ParserError, UnicodeDecodeError, ValueError, OSError):
                st.error("El archivo subido no es un archivo CSV válido.")
                return

            try:
                importadas = Cartera()
                cantidad = importadas.importar_dataframe(df)
            except KeyError:
                st.error(
                    "Las columnas esperadas son: "
                    "descripción, monto, fecha, categoria, tipo."
                )
                return
            except (TypeError, ValueError):
                st.error("El CSV contiene valores inválidos en monto o fecha.")
                return

            repositorio.agregar_transacciones(user_id, importadas.transacciones)
            st.session_state.cartera.agregar_transacciones(
                importadas.transacciones
            )
            st.success(f"Se importaron {cantidad} transacciones correctamente.")


def borrar_movimientos(repositorio: RepositorioSupabase, user_id: str):
    if st.button("Borrar movimientos"):
        repositorio.borrar_transacciones(user_id)
        st.session_state.cartera.borrar_transacciones()
        st.success("Tus movimientos fueron borrados correctamente.")


def mostrar_formulario(repositorio: RepositorioSupabase, user_id: str):
    with st.form("nueva_transaccion"):
        descripcion = st.text_input("Descripción del gasto o ingreso:")
        monto_str = st.text_input("Monto (ej. 1,000.00):", value="")
        fecha = st.date_input("Fecha:")
        categoria = st.selectbox("Categoría:", categorias)
        tipo = st.radio("Tipo de operación:", ["Ingreso", "Gasto"], horizontal=True)
        enviado = st.form_submit_button("Enviar")

    if enviado:
        try:
            monto = Cartera.parsear_monto(monto_str)
        except ValueError:
            st.error("Por favor, ingresa un monto válido (ejemplo: 1,000.00).")
            return

        if not Cartera.monto_es_positivo(monto):
            st.error("Por favor, ingresa un monto mayor a 0.")
            return

        transaccion = Transaccion(descripcion, monto, fecha, categoria, tipo)
        repositorio.agregar_transacciones(user_id, [transaccion])
        st.session_state.cartera.agregar_transaccion(transaccion)
        st.success("Transacción registrada exitosamente.")


def mostrar_filtros(cartera):
    fecha_desde, fecha_hasta = cartera.rango_fechas()

    categorias_seleccionadas = st.multiselect(
        "Categorías", options=categorias, default=categorias
    )
    fecha_desde = st.date_input("Desde", value=fecha_desde)
    fecha_hasta = st.date_input("Hasta", value=fecha_hasta)

    return categorias_seleccionadas, fecha_desde, fecha_hasta


def mostrar_transacciones(cartera, repositorio, user_id):
    st.subheader("Transacciones Registradas")

    if cartera.transacciones:
        columnas = st.columns([3, 1.3, 1.2, 1.5, 1, 0.9])
        for columna, titulo in zip(
            columnas, ["Descripción", "Monto", "Fecha", "Categoría", "Tipo", ""]
        ):
            columna.markdown(f"**{titulo}**")

        for transaccion in list(cartera.transacciones):
            columnas = st.columns([3, 1.3, 1.2, 1.5, 1, 0.9])
            columnas[0].write(transaccion.descripcion)
            columnas[1].write(f"${transaccion.monto:,.2f}")
            columnas[2].write(transaccion.fecha.isoformat())
            columnas[3].write(transaccion.categoria)
            columnas[4].write(transaccion.tipo)
            borrar = columnas[5].button(
                "Borrar",
                key=f"borrar_transaccion_{transaccion.id}",
                disabled=transaccion.id is None,
            )
            if borrar and transaccion.id is not None:
                repositorio.borrar_transaccion(user_id, transaccion.id)
                st.session_state.cartera.eliminar_transaccion(transaccion.id)
                cartera.transacciones.remove(transaccion)
                st.success("El movimiento fue borrado correctamente.")

        st.download_button(
            "Descargar Transacciones",
            data=cartera.a_csv(),
            file_name="mis_transacciones.csv",
            mime="text/csv",
        )
    else:
        st.info("No hay transacciones registradas.")


def mostrar_resumen(cartera):
    if not cartera.transacciones:
        st.info("No hay transacciones para mostrar.")
        return

    resumen = cartera.resumen()
    columnas = st.columns(2)
    columnas[0].metric("Ingresos:", f"${resumen['ingresos']:,.2f}")
    columnas[1].metric("Gastos:", f"${resumen['gastos']:,.2f}")
    columnas = st.columns(2)
    columnas[0].metric("Balance:", f"${resumen['balance']:,.2f}")
    columnas[1].metric("Gasto promedio:", f"${resumen['gasto_promedio']:,.2f}")


def mostrar_analisis(cartera):
    gastos_por_categoria = cartera.gastos_por_categoria()
    gastos_por_fecha = cartera.gastos_por_fecha()

    if not gastos_por_categoria:
        st.info("No hay transacciones de tipo Gasto para analizar.")
        return

    df_categorias = pd.DataFrame(
        list(gastos_por_categoria.items()),
        columns=["Categoría", "Total de gastos"],
    )
    st.subheader("Total de gastos por categoría")
    st.bar_chart(df_categorias, x="Categoría", y="Total de gastos")

    df_fechas = pd.DataFrame(
        sorted(gastos_por_fecha.items()),
        columns=["Fecha", "Total de gastos"],
    )
    st.subheader("Total de gastos por fecha")
    st.line_chart(df_fechas, x="Fecha", y="Total de gastos")


def main():
    mostrar_titulos()

    if "supabase_client" not in st.session_state:
        st.session_state.supabase_client = crear_cliente_supabase()
    cliente = st.session_state.supabase_client

    if "user_id" not in st.session_state:
        iniciar_sesion(cliente)
        return

    user_id = st.session_state.user_id
    repositorio = RepositorioSupabase(cliente)
    inicializar_cartera(repositorio, user_id)
    mostrar_cerrar_sesion(cliente)

    with st.sidebar:
        mostrar_formulario(repositorio, user_id)
        importar_csv(repositorio, user_id)
        borrar_movimientos(repositorio, user_id)
        categorias_seleccionadas, fecha_desde, fecha_hasta = mostrar_filtros(
            st.session_state.cartera
        )

    cartera_filtrada = st.session_state.cartera.filtrar(
        categorias_seleccionadas, fecha_desde, fecha_hasta
    )

    tab_resumen, tab_movimientos, tab_analisis = st.tabs(
        ["Resumen", "Movimientos", "Análisis"]
    )

    with tab_resumen:
        mostrar_resumen(cartera_filtrada)

    with tab_movimientos:
        mostrar_transacciones(cartera_filtrada, repositorio, user_id)

    with tab_analisis:
        mostrar_analisis(cartera_filtrada)


if __name__ == "__main__":
    main()
