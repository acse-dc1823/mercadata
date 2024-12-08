import os
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from process_data import process_pdfs  # Solo importamos process_pdfs

# Configuración de la página de Streamlit
st.set_page_config(
    page_title="Mercadona Data Analysis",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Ruta del archivo CSV y del logo
csv_path = "data/mercadata.csv"
logo_path = "images/logo.png"  # Cambia esto a la ubicación de tu archivo de logo

# Mostrar el logo como banner en la parte superior
if os.path.exists(logo_path):
    st.image(logo_path, width=600)  # Ajusta el ancho del logo según tu preferencia
else:
    st.warning(f"Logo no encontrado en {logo_path}")

# Subir archivos PDF
uploaded_files = st.file_uploader("Sube tus archivos PDF", type="pdf", accept_multiple_files=True)

if uploaded_files:
    st.success(f"Has subido {len(uploaded_files)} archivo(s) PDF.")

    # Procesar los archivos PDF cuando el botón es presionado
    if st.button("Procesar PDFs"):
        try:
            # Pasar los archivos PDF a la función de procesamiento
            process_pdfs(uploaded_files)  # Asegúrate de que esta función esté bien definida en process_data.py
            st.success("Archivos PDF procesados correctamente.")
        except Exception as e:
            st.error(f"Error al procesar los archivos PDF: {e}")
else:
    st.warning("Por favor, sube al menos un archivo PDF para continuar.")

# Barra lateral
with st.sidebar:
    st.title('🛒 Mercadona Data Analysis')
    

    # Filtro por meses
    if os.path.exists(csv_path):
        try:
            data = pd.read_csv(csv_path)
            data["fecha"] = pd.to_datetime(data["fecha"], format="%d/%m/%Y %H:%M", dayfirst=True)
            data.set_index("fecha", inplace=True)
            
            month_start_dates = data.index.to_period("M").to_timestamp().drop_duplicates().sort_values()
            selected_month_start = st.selectbox("Selecciona el mes", month_start_dates.strftime('%Y-%m'), index=0)
            selected_month_start = pd.Timestamp(selected_month_start)
            filtered_data_by_month = data[data.index.to_period("M").start_time == selected_month_start]
            
            # Filtro por categoría
            selected_category = st.selectbox("Selecciona la categoría", data["categoría"].unique())
            filtered_data_by_categories = data[data["categoría"] == selected_category]
        except Exception as e:
            st.error(f"Error al leer el archivo CSV: {e}")
    else:
        st.error(f"Archivo {csv_path} no encontrado. Asegúrate de que `process_data.py` haya sido ejecutado correctamente.")

    st.subheader("Sobre la Aplicación")
    st.write('''
        - Esta aplicación pretende analizar los patrones de gasto en diferentes categorías y a lo largo del tiempo.
    ''')

# Verificar si el archivo CSV existe y no está vacío
if os.path.exists(csv_path):
    try:
        data = pd.read_csv(csv_path)
        if not data.empty:
            data["fecha"] = pd.to_datetime(data["fecha"], format="%d/%m/%Y %H:%M", dayfirst=True)
            data.set_index("fecha", inplace=True)

            # Métricas relevantes
            total_spent = data["precio"].sum()
            total_purchases = data["identificativo de ticket"].nunique()
            avg_spent_per_purchase = data.groupby("identificativo de ticket")["precio"].sum().mean()
            category_with_highest_spent = data.groupby("categoría")["precio"].sum().idxmax()
            total_items_sold = data['item'].nunique()
            avg_spent_per_month = data["precio"].resample('M').sum().mean()
            total_tickets_per_month = data.groupby(data.index.to_period('M')).size().mean()

            # Crear columnas para las métricas
            col1, col2, col3 = st.columns(3)

            # Mostrar las métricas en las columnas
            with col1:
                st.metric(label="Gasto Total", value=f"€{total_spent:.2f}")
                st.metric(label="Gasto Promedio por Compra", value=f"€{avg_spent_per_purchase:.2f}")
                st.metric(label="Número Total de Compras", value=total_purchases)
                st.metric(label="Items Vendidos", value=total_items_sold)

            with col2:
                st.metric(label="Categoría con Mayor Gasto", value=category_with_highest_spent)
                st.metric(label="Gasto Promedio Mensual", value=f"€{avg_spent_per_month:.2f}")
                st.metric(label="Items por Mes", value=f"{total_tickets_per_month:.2f}")

            with col3:
                st.metric(label="Total Gastado en el Mes Seleccionado", value=f"€{filtered_data_by_month['precio'].sum():.2f}")
                st.metric(label="Número de Compras en el Mes Seleccionado", value=filtered_data_by_month['identificativo de ticket'].nunique())
                st.metric(label="Categoría con Mayor Gasto en el Mes Seleccionado", value=filtered_data_by_month.groupby("categoría")["precio"].sum().idxmax())

            # Crear una sola fila con el gráfico de distribución del gasto por categoría (Pie Chart)
            st.subheader("Distribución del Gasto")
            col1 = st.columns(1)[0]
            with col1:
                # Distribución del Gasto por Categoría
                total_price_per_category = data.groupby("categoría")["precio"].sum().reset_index()
                fig_pie = px.pie(total_price_per_category, values='precio', names='categoría', title='Distribución del Gasto por Categoría')
                st.plotly_chart(fig_pie)

            # Crear una segunda fila con los gráficos de gasto total por mes y precio medio por categoría
            st.subheader("Análisis de Gasto por Tiempo y Categoría")
            col1, col2 = st.columns(2)

            with col1:
                # Gasto Total por Mes
                monthly_expense = data["precio"].resample('M').sum().reset_index()
                fig_bar = px.bar(monthly_expense, x='fecha', y='precio', labels={'fecha': 'Mes', 'precio': 'Gasto (€)'})
                st.plotly_chart(fig_bar)

            with col2:
                # Precio Medio por Categoría
                avg_price_per_category = data.groupby("categoría")["precio"].mean().reset_index().sort_values(by="precio", ascending=False)
                fig_bar_avg = px.bar(avg_price_per_category, x='categoría', y='precio', labels={'precio': 'Precio Medio (€)'})
                st.plotly_chart(fig_bar_avg)


            # Análisis del Gasto en el Tiempo y Top 10 Items
            col1, col2 = st.columns(2)

            with col1:
                # Gasto Total por Semana
                weekly_expense = data["precio"].resample('W').sum().reset_index()  # Resample to weekly
                fig_weekly_bar = px.bar(
                    weekly_expense,
                    x='fecha',
                    y='precio',
                    labels={'fecha': 'Semana', 'precio': 'Gasto (€)'},
                    title='Gasto Total por Semana'
                )
                fig_weekly_bar.update_layout(xaxis_title='Semana', yaxis_title='Gasto (€)')
                st.plotly_chart(fig_weekly_bar)


            with col2:
                # Top 10 Items con Mayor Gasto
                top_items = data.groupby('item')['precio'].sum().nlargest(10).reset_index()
                fig_top_items = px.bar(top_items, x='item', y='precio', labels={'item': 'Item', 'precio': 'Gasto (€)'},
                                       title='Top 10 Items con Mayor Gasto')
                st.plotly_chart(fig_top_items)

            # Datos Filtrados
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Datos Filtrados por Categorías")
                st.dataframe(filtered_data_by_categories)

            with col2:
                st.subheader("Datos Filtrados por Mes")
                st.dataframe(filtered_data_by_month)

            # Heatmap del gasto por día y hora
            st.subheader("Heatmap del Gasto por Día y Hora")
            # Ensure 'hour_of_day' is limited to the opening hours (9 to 23)
            data['day_of_week'] = data.index.dayofweek
            data['hour_of_day'] = data.index.hour

            # Filter data for hours between 9 and 23
            data_filtered = data[(data['hour_of_day'] >= 9) & (data['hour_of_day'] <= 22)]

            # Create a range of hours from 9 to 23 and days of the week
            hours = list(range(9, 23))
            days = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']

            # Create the pivot table with the filtered data
            heatmap_data = data_filtered.pivot_table(
                values='precio',
                index='hour_of_day',
                columns='day_of_week',
                aggfunc='sum',
                fill_value=0
            ).reindex(index=hours, columns=range(7), fill_value=0)  # Ensure full range of hours and days

            # Create the heatmap
            fig_heatmap = go.Figure(
                data=go.Heatmap(
                    z=heatmap_data.values,
                    x=days,  # Day names
                    y=hours,  # Limited to 9-23
                    colorscale='Viridis'
                )
            )

            # Update layout
            fig_heatmap.update_layout(
                xaxis_title='Día de la Semana',
                yaxis_title='Hora del Día',
                yaxis=dict(dtick=1)  # Ensure ticks for every hour
            )

            # Display the heatmap
            st.plotly_chart(fig_heatmap)


        else:
            st.warning("El archivo CSV está vacío. Por favor, asegúrate de que `process_data.py` haya generado datos correctamente.")
    
    except Exception as e:
        st.error(f"Error al leer el archivo CSV: {e}")
else:
    st.error(f"Archivo {csv_path} no encontrado. Asegúrate de que `process_data.py` haya sido ejecutado correctamente.")