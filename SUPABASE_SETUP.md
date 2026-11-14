# Configuración de cuentas y base de datos

La aplicación usa Supabase Auth para las cuentas y una tabla con políticas RLS
para que cada usuario solo pueda leer, agregar o borrar sus propias transacciones.
No se debe configurar una clave `service_role` en la aplicación.

## Preparar Supabase

1. Crea un proyecto en [supabase.com](https://supabase.com/).
2. En **SQL Editor**, ejecuta el contenido de `supabase_schema.sql`.
3. En **Project Settings > API**, copia la URL del proyecto y la clave pública
   (publishable/anon). Nunca uses la clave `service_role`.
4. En **Authentication > URL Configuration**, configura las URL de redirección
   de tu sitio cuando se despliegue. Para el flujo actual de correo y contraseña
   no se necesita configurar OAuth.
5. Si la confirmación de correo está activa, los usuarios deberán confirmar el
   mensaje de Supabase antes de iniciar sesión.

## Ejecutar localmente

Instala dependencias:

```powershell
python -m pip install -r requirements.txt
```

Crea `.streamlit\secrets.toml` (no lo publiques ni lo agregues al repositorio):

```toml
[supabase]
url = "https://TU-PROYECTO.supabase.co"
anon_key = "TU-CLAVE-PUBLICA"
```

Inicia la aplicación:

```powershell
streamlit run app.py
```

## Publicar

Publica el código en un repositorio privado o público de GitHub, excluyendo
`.venv`, `.streamlit\secrets.toml` y cualquier archivo con datos personales.
En Streamlit Community Cloud, crea una app desde ese repositorio y configura
los mismos valores en **App settings > Secrets**, usando formato TOML:

```toml
[supabase]
url = "https://TU-PROYECTO.supabase.co"
anon_key = "TU-CLAVE-PUBLICA"
```

La aplicación es Streamlit; Netlify no ejecuta una app Python persistente de
Streamlit. Usa un host compatible con Streamlit.

## Datos existentes

`transacciones.csv` no se importa automáticamente porque no se sabe a qué cuenta
pertenecen sus filas. Después de crear una cuenta, cada usuario puede importar
su propio CSV desde la aplicación.
