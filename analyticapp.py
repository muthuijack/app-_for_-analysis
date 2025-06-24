import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from fpdf import FPDF
import io
import base64
import os
import squarify  # for treemap

# Setup
st.set_page_config(page_title="Data Explorer", layout="wide")
sns.set_style("whitegrid")

# Custom Header UI
with st.container():
    st.markdown(
        """
        <div style="background-color:#0e1117;padding:15px 25px;border-radius:12px;margin-bottom:10px">
            <h1 style="color:white;font-size:32px;margin:0">📊 Data Visualization Studio</h1>
            <p style="color:#9ca3af;font-size:16px;margin:0">Explore, visualize, and transform your data interactively</p>
        </div>
        """,
        unsafe_allow_html=True
    )

# Upload CSV
uploaded_file = st.file_uploader("📁 Upload your CSV file", type=["csv"])
if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df_copy = df.copy()

    # Detect date-like columns
    date_cols = []
    for col in df.columns:
        if df[col].dtype == 'object':
            try:
                if df[col].str.contains(r"[\/\.\-, ]").any():
                    date_cols.append(col)
            except:
                continue

    # Tabs in specified order
    tab_names = ["🔍 Preview", "🛠️ Transform", "💡 Chart Guide"]
    if date_cols:
        tab_names.append("📅 Time Series")
    tab_names.append("📊 Visuals")
    tab_names.append("📤 Export PDF")

    tabs = st.tabs(tab_names)

    tab_preview = tabs[0]
    tab_transform = tabs[1]
    tab_guide = tabs[2]
    tab_time = tabs[3] if date_cols else None
    tab_visuals = tabs[4 if date_cols else 3]
    tab_pdf = tabs[5 if date_cols else 4]

    # Time Series Tab with safe handling
    if tab_time:
        with tab_time:
            st.subheader("📅 Time Series Analysis")

            date_col = st.selectbox("Select a date/time column:", date_cols)
            numeric_cols = df.select_dtypes(include='number').columns.tolist()

            if numeric_cols:
                value_col = st.selectbox("Select numeric column to plot:", numeric_cols)
            else:
                st.warning("⚠️ No numeric columns available for plotting.")
                value_col = None

            try:
                df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
                if value_col:
                    df_sorted = df[[date_col, value_col]].dropna().sort_values(by=date_col)
                    if not df_sorted.empty:
                        st.line_chart(df_sorted.set_index(date_col)[value_col])
                    else:
                        st.warning("No valid data to plot after cleaning.")
            except KeyError as e:
                st.error(f"Column not found: {e}")
            except Exception as e:
                st.error(f"Could not generate time series chart: {e}")

    # Visuals tab retained (enhanced with dropdown chart selector)
    chart_buffers = []
    with tab_visuals:
        st.subheader("📊 Interactive Chart Builder")

        selected_cols = st.multiselect("Select columns to visualize:", df.columns)
        chart_type = st.selectbox("Select chart type:", [
            "Histogram", "Pie Chart", "Bar Chart", "Line Chart", "Boxplot", "Scatter Plot", "Violin Plot", "KDE Plot",
            "Heatmap", "Pairplot", "Treemap", "Area Chart", "Correlation Matrix",
            "Donut Chart", "Hexbin Plot"
        ])

        if selected_cols:
            try:
                fig, ax = plt.subplots(figsize=(10, 6))
                if chart_type == "Histogram":
                    sns.histplot(df[selected_cols[0]].dropna(), kde=True, ax=ax)
                elif chart_type == "Pie Chart":
                    df[selected_cols[0]].value_counts().plot(kind="pie", autopct="%1.1f%%", ax=ax)
                    ax.set_ylabel("")
                elif chart_type == "Bar Chart":
                    df[selected_cols[0]].value_counts().plot(kind="bar", ax=ax)
                elif chart_type == "Line Chart" and len(selected_cols) >= 2:
                    df.plot(x=selected_cols[0], y=selected_cols[1], ax=ax)
                elif chart_type == "Boxplot" and len(selected_cols) >= 2:
                    sns.boxplot(x=df[selected_cols[0]], y=df[selected_cols[1]], ax=ax)
                elif chart_type == "Scatter Plot" and len(selected_cols) >= 2:
                    sns.scatterplot(x=df[selected_cols[0]], y=df[selected_cols[1]], ax=ax)
                elif chart_type == "Violin Plot" and len(selected_cols) >= 2:
                    sns.violinplot(x=df[selected_cols[0]], y=df[selected_cols[1]], ax=ax)
                elif chart_type == "KDE Plot" and len(selected_cols) >= 2:
                    sns.kdeplot(x=df[selected_cols[0]], y=df[selected_cols[1]], fill=True, ax=ax)
                elif chart_type == "Heatmap":
                    numeric_df = df[selected_cols].select_dtypes(include='number')
                    if not numeric_df.empty:
                        sns.heatmap(numeric_df.corr(), annot=True, cmap="coolwarm", ax=ax)
                elif chart_type == "Pairplot":
                    numeric_df = df[selected_cols].select_dtypes(include='number')
                    if not numeric_df.empty:
                        pairplot_fig = sns.pairplot(numeric_df)
                        chart_buffers.append(pairplot_fig.figure)
                        st.pyplot(pairplot_fig.figure)
                        return
                elif chart_type == "Treemap":
                    num_data = df[selected_cols[0]].fillna(0).values if selected_cols else []
                    labels = df.index.astype(str).tolist()
                    fig = plt.figure(figsize=(10, 6))
                    squarify.plot(sizes=num_data, label=labels, alpha=.8)
                elif chart_type == "Area Chart":
                    numeric_df = df[selected_cols].select_dtypes(include='number')
                    if not numeric_df.empty:
                        st.area_chart(numeric_df)
                        return
                elif chart_type == "Correlation Matrix":
                    numeric_df = df[selected_cols].select_dtypes(include='number')
                    if not numeric_df.empty:
                        st.dataframe(numeric_df.corr())
                        return
                elif chart_type == "Donut Chart":
                    cat_col = selected_cols[0]
                    if df[cat_col].dtype == 'object':
                        sizes = df[cat_col].value_counts()
                        labels = sizes.index.tolist()
                        fig, ax = plt.subplots()
                        ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, wedgeprops=dict(width=0.4))
                        ax.axis('equal')
                elif chart_type == "Hexbin Plot":
                    numeric_cols = df[selected_cols].select_dtypes(include='number').columns.tolist()
                    if len(numeric_cols) >= 2:
                        fig, ax = plt.subplots()
                        ax.hexbin(df[numeric_cols[0]], df[numeric_cols[1]], gridsize=30, cmap='Blues')
                        ax.set_xlabel(numeric_cols[0])
                        ax.set_ylabel(numeric_cols[1])
                st.pyplot(fig)
                chart_buffers.append(fig)
            except Exception as e:
                st.error(f"Chart creation error: {e}")

    # Export PDF Tab
    with tab_pdf:
        st.subheader("📤 Export Visualizations to PDF")

        if chart_buffers:
            if st.button("📥 Download PDF Report"):
                pdf = FPDF()
                pdf.set_auto_page_break(auto=True, margin=15)
                for fig in chart_buffers:
                    img_buffer = io.BytesIO()
                    fig.savefig(img_buffer, format='png')
                    img_buffer.seek(0)

                    img_path = os.path.join("temp_chart.png")
                    with open(img_path, "wb") as f:
                        f.write(img_buffer.getbuffer())

                    pdf.add_page()
                    pdf.image(img_path, x=10, y=30, w=180)

                pdf_output = io.BytesIO()
                pdf.output(pdf_output)
                b64 = base64.b64encode(pdf_output.getvalue()).decode()
                href = f'<a href="data:application/pdf;base64,{b64}" download="charts_report.pdf">📄 Download PDF</a>'
                st.markdown(href, unsafe_allow_html=True)
        else:
            st.info("📊 No charts available to export. Please generate visualizations first.")
else:
    st.info("📁 Upload a CSV file to begin.")
