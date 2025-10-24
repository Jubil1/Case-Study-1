# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
from pathlib import Path
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

st.set_page_config(page_title="Filipino Emigrant Data", layout="wide")
st.title("Visualizing Four Decades of Filipino Emigration")


# ---------- Helper for displaying datasets ----------
def show_df_info(df, label):
    st.write(f"✅ {label}: {df.shape[0]} rows × {df.shape[1]} columns")
    st.dataframe(df.head(10), width="stretch")
    st.divider()

# --------- Story Time -------
def display_story_intro():
    st.header("📖 Overview — The Story of Filipino Emigration (1981–2020)")
    st.markdown(
        """
        **Why this matters.**  
        The Philippines is one of the world's major sources of international migrants.  
        This case study uses official registered-emigrant data (Commission on Filipinos Overseas) to explore
        who migrated, where they went, and how patterns changed over four decades (1981–2020).

        **What you'll see.**  
        - A raw-data peek to show common data issues and why cleaning is necessary.  
        - Cleaned datasets for each dimension (age, sex, education, occupation, civil status, origin, destinations).  
        - Visualizations that highlight comparisons, compositions, trends, distributions, relationships, and geography.

        **How to use this app.**  
        Use the tabs to navigate sections. Start here to understand the story and then move to the dataset tabs to inspect
        raw/cleaned data and charts. After exploring each tab, return to the **Insights & Conclusions** (later) for a concise summary.
        """
    )

# ---------- 1️⃣ AGE FILE ----------
def display_age_data():
    st.header("🧒 Emigrant-1981-2020-Age.xlsx")

    path = Path(__file__).parent / "Emigrant-1981-2020-Age.xlsx"

    # --- STEP 1: Show RAW dataset ---
    st.subheader("📂 Raw Dataset Preview")

    try:
        raw_df = pd.read_excel(path, engine="openpyxl")
        # Convert all columns to strings for safe display (fixes ArrowTypeError)
        raw_df = raw_df.astype(str)
        st.dataframe(raw_df.head(10), width="stretch")
        st.caption("👀 Raw data (first 10 rows)")
    except Exception as e:
        st.error(f"Error loading raw dataset: {e}")

    st.divider()

    # --- STEP 2: Explain Cleaning Process ---
    st.subheader("🧹 Cleaning Process Overview")
    st.write("""
    To make the dataset ready for analysis, we performed the following steps:
    1. Skipped unnecessary header rows  
    2. Renamed and standardized column labels  
    3. Removed empty or irrelevant rows  
    4. Converted all numerical values to integers  
    """)

    st.divider()

    # --- STEP 3: Load CLEANED dataset ---
    st.subheader("✅ Cleaned Dataset Preview")
    try:
        df = pd.read_excel(path, header=2, engine="openpyxl")
        df.columns = df.columns.map(str)
        show_df_info(df, "Cleaned Age dataset ready for analysis")

        # --- STEP 4: Visualization ---
        st.divider()
        st.subheader("📊 Trend Visualization: Total Emigrants by Age Group Over Time")

        # Reshape for plotting
        df_melted = df.melt(id_vars=df.columns[0], var_name="Year", value_name="Emigrants")
        df_melted = df_melted[df_melted["Year"].str.match(r"^\d{4}$")]  # keep only years
        df_melted["Year"] = df_melted["Year"].astype(int)

        fig = px.line(
            df_melted,
            x="Year",
            y="Emigrants",
            color=df.columns[0],
            markers=True,
            title="Trends in Filipino Emigrants by Age Group (1981–2020)",
        )

        fig.update_layout(
            xaxis_title="Year",
            yaxis_title="Number of Emigrants",
            legend_title="Age Group",
            height=500,
        )

        st.plotly_chart(fig, use_container_width=True)
        st.caption("📈 This line chart shows how different age groups contributed to total emigration across the years.")

    except Exception as e:
        st.error(f"Error loading cleaned dataset or visualization: {e}")


# ---------- 2️⃣ ALL COUNTRIES FILE ----------
def display_country_data():
    import pycountry  # ✅ added for country code conversion

    st.header("🌍 Emigrant-1981-2020-AllCountries.xlsx")

    path = Path(__file__).parent / "Emigrant-1981-2020-AllCountries.xlsx"

    # --- STEP 1: Show RAW dataset ---
    st.subheader("📂 Raw Dataset Preview")

    try:
        raw_df = pd.read_excel(path, engine="openpyxl")
        raw_df = raw_df.astype(str)
        st.dataframe(raw_df.head(10), width="stretch")
        st.caption("👀 Raw data (first 10 rows) — Notice unfiltered entries and formatting issues.")
    except Exception as e:
        st.error(f"Error loading raw dataset: {e}")

    st.divider()

    # --- STEP 2: Explain Cleaning Process ---
    st.subheader("🧹 Cleaning Process Overview")
    st.write("""
    To make this dataset ready for visualization, the following cleaning steps were applied:
    1. Skipped unnecessary header rows  
    2. Renamed the first column as **COUNTRY**  
    3. Removed total, 'Others', and unknown categories  
    4. Converted yearly values to numeric types  
    5. Computed the total emigrants per country  
    """)

    st.divider()

    # --- STEP 3: Load and Clean the Dataset ---
    st.subheader("✅ Cleaned Dataset Preview")
    try:
        df = pd.read_excel(path, header=2, engine="openpyxl")
        df.columns = df.columns.map(str)
        df = df.dropna(how="all").dropna(axis=1, how="all")

        if "COUNTRY" not in df.columns:
            df.rename(columns={df.columns[0]: "COUNTRY"}, inplace=True)

        df = df[df["COUNTRY"].notna()]
        df["COUNTRY"] = df["COUNTRY"].astype(str).str.strip()
        df = df[~df["COUNTRY"].str.contains("TOTAL|OTHERS|UNKNOWN", case=False, na=False)]

        numeric_cols = [c for c in df.columns if c != "COUNTRY"]
        df[numeric_cols] = (
            df[numeric_cols].apply(pd.to_numeric, errors="coerce").fillna(0).astype(int)
        )

        df = df.drop_duplicates(subset="COUNTRY")
        df["Total_Emigrants"] = df[numeric_cols].sum(axis=1)

        show_df_info(df, "Cleaned AllCountries dataset ready for analysis")

        st.divider()

        # --- STEP 4: Add ISO-3 country codes ---
        def country_to_iso3(country_name):
            try:
                return pycountry.countries.lookup(country_name).alpha_3
            except:
                return None

        df["ISO3"] = df["COUNTRY"].apply(country_to_iso3)
        df = df[df["ISO3"].notna()]  # remove unmatched countries

        # --- STEP 5: Geographic Representation (Choropleth Map) ---
        st.subheader("🗺️ Geographic Representation: Global Emigrant Distribution")

        fig_map = px.choropleth(
            df,
            locations="ISO3",
            locationmode="ISO-3",
            color="Total_Emigrants",
            hover_name="COUNTRY",
            color_continuous_scale="Viridis",
            title="Global Distribution of Filipino Emigrants (1981–2020)",
        )

        fig_map.update_layout(
            geo=dict(showframe=False, showcoastlines=True, projection_type="natural earth"),
            height=600,
            margin=dict(l=0, r=0, t=50, b=0),
        )

        st.plotly_chart(fig_map, use_container_width=True)
        st.caption("🗺️ This choropleth map shows the total number of Filipino emigrants by country of destination (1981–2020).")

    except Exception as e:
        st.error(f"Error cleaning or visualizing dataset: {e}")

# ---------- 3️⃣ MAJOR COUNTRY FILE ----------
def display_major_country_data():
    st.header("🏆 Emigrant-1981-2020-MajorCountry.xlsx")

    path = Path(__file__).parent / "Emigrant-1981-2020-MajorCountry.xlsx"

    # --- STEP 1: Show RAW dataset ---
    st.subheader("📂 Raw Dataset Preview")

    try:
        raw_df = pd.read_excel(path, engine="openpyxl")
        raw_df = raw_df.astype(str)  # ✅ Fix ArrowTypeError
        st.dataframe(raw_df.head(10), width="stretch")
        st.caption("👀 Raw data (first 10 rows) — notice uncleaned totals and mixed data formats.")
    except Exception as e:
        st.error(f"Error loading raw dataset: {e}")
        return

    st.divider()

    # --- STEP 2: Cleaning Process Overview ---
    st.subheader("🧹 Cleaning Process Overview")
    st.write("""
    To prepare the dataset for analysis, we:
    1. Skipped unnecessary header rows  
    2. Standardized column names  
    3. Converted yearly data into numeric values  
    4. Removed empty and irrelevant rows  
    """)

    st.divider()

    # --- STEP 3: Load and Clean Data ---
    st.subheader("✅ Cleaned Dataset Preview")

    try:
        df = pd.read_excel(path, header=2, engine="openpyxl").dropna(axis=1, how="all")

        expected_cols = [
            "YEAR", "USA", "CANADA", "JAPAN", "AUSTRALIA", "ITALY",
            "NEW_ZEALAND", "UNITED_KINGDOM", "GERMANY", "SOUTH_KOREA",
            "SPAIN", "OTHERS", "TOTAL", "_Inc_Dec"
        ]
        if len(df.columns) == len(expected_cols):
            df.columns = expected_cols

        df = df.dropna(how="all")
        df = df[df["YEAR"].notna()]
        df["YEAR"] = df["YEAR"].astype(str).str.strip()

        numeric_cols = [c for c in df.columns if c != "YEAR"]
        df[numeric_cols] = (
            df[numeric_cols].apply(pd.to_numeric, errors="coerce").fillna(0).astype(int)
        )

        show_df_info(df, "Cleaned MajorCountry dataset ready for analysis")

        st.divider()

        # --- STEP 4: Bar Chart of Cumulative Totals ---
        st.subheader("📊 Total Filipino Emigrants by Major Destination (1981–2020)")

        # ✅ Include all valid country columns except TOTAL, % Inc.(Dec.), or Unnamed
        exclude_keywords = ["TOTAL", "INC", "UNNAMED"]
        country_columns = [
            c for c in df.columns
            if c != "YEAR" and not any(ex in c.upper() for ex in exclude_keywords)
        ]

        # ✅ Compute cumulative totals
        df_totals = (
            df[country_columns]
            .sum()
            .reset_index()
            .rename(columns={"index": "Country", 0: "Total_Emigrants"})
        )

        # --- Visualization ---
        fig_bar = px.bar(
            df_totals.sort_values("Total_Emigrants", ascending=False),
            x="Country",
            y="Total_Emigrants",
            text="Total_Emigrants",
            title="Total Filipino Emigrants by Major Destination (1981–2020)",
            color="Country",
        )

        fig_bar.update_traces(texttemplate="%{text:,}", textposition="outside")
        fig_bar.update_layout(
            xaxis_title="Country",
            yaxis_title="Total Emigrants",
            showlegend=True,
            legend_title_text="Country",
            height=500,
        )

        st.plotly_chart(fig_bar, use_container_width=True)

    except Exception as e:
        st.error(f"Error cleaning or visualizing dataset: {e}")

# ------- Occupation File ------
def display_occu_data():
    st.header("💼 Emigrant-1981-2020-Occu.xlsx")

    path = Path(__file__).parent / "Emigrant-1981-2020-Occu.xlsx"

    # --- STEP 1: Show RAW dataset ---
    st.subheader("📂 Raw Dataset Preview")

    try:
        raw_df = pd.read_excel(path, engine="openpyxl")
        raw_df = raw_df.astype(str)
        st.dataframe(raw_df.head(10), width="stretch")
        st.caption("👀 Raw data (first 10 rows) — notice unstandardized formatting or totals.")
    except Exception as e:
        st.error(f"Error loading raw dataset: {e}")
        return

    st.divider()

    # --- STEP 2: Cleaning Overview ---
    st.subheader("🧹 Cleaning Process Overview")
    st.write("""
    To prepare the dataset:
    1. Skipped extra header rows  
    2. Standardized column names  
    3. Converted yearly columns to numeric  
    4. Removed blank rows and irrelevant totals  
    """)

    st.divider()

    # --- STEP 3: Load & Clean Data ---
    st.subheader("✅ Cleaned Dataset Preview")

    try:
        df = (
            pd.read_excel(path, header=2, engine="openpyxl")
            .dropna(axis=1, how="all")
            .dropna(how="all")
        )

        expected_cols = [
            "MAJOR_OCCUPATION_GROUP", *map(str, range(1981, 2021)), "TOTAL"
        ]

        if len(df.columns) >= len(expected_cols):
            df = df.iloc[:, :len(expected_cols)]
            df.columns = expected_cols

        df = df[df["MAJOR_OCCUPATION_GROUP"].notna()]
        df["MAJOR_OCCUPATION_GROUP"] = df["MAJOR_OCCUPATION_GROUP"].astype(str).str.strip()

        numeric_cols = [c for c in df.columns if c != "MAJOR_OCCUPATION_GROUP"]
        df[numeric_cols] = (
            df[numeric_cols].apply(pd.to_numeric, errors="coerce").fillna(0).astype(int)
        )

        show_df_info(df, "Cleaned Occupation dataset ready for visualization")

        st.divider()

        # --- STEP 4: Improved Grouped Bar Chart (Employed vs Unemployed Only) ---
        st.subheader("🏗️ Multi-set Bar Chart: Employed vs. Unemployed Occupations")

        st.write("""
        This visualization separates **Employed** and **Unemployed** groups,
        then compares their subcategories every 5 years from 1981–2020.
        """)

        # Define categories
        employed = [
            "Prof'l, Tech'l, & Related Workers",
            "Managerial, Executive, and Administrative Workers",
            "Clerical Workers",
            "Sales Workers",
            "Service Workers",
            "Agri, Animal Husbandry, Forestry Workers & Fishermen",
            "Production Process, Transport Equipment Operators, & Laborers",
            "Members of the Armed Forces",
        ]

        unemployed = [
            "Housewives",
            "Retirees",
            "Students",
            "Minors (Below 7 years old)",
            "Out of School Youth",
            "Refugees",
            "No Occupation Reported",
        ]

        # Tag category (only Employed or Unemployed)
        df["CATEGORY"] = df["MAJOR_OCCUPATION_GROUP"].apply(
            lambda x: "Employed" if x in employed else ("Unemployed" if x in unemployed else None)
        )

        # Filter out rows that are neither employed nor unemployed
        df_filtered = df[df["CATEGORY"].notna() & ~df["MAJOR_OCCUPATION_GROUP"].str.contains("TOTAL", case=False, na=False)]

        # Select every 5 years for clarity
        selected_years = [str(y) for y in range(1981, 2021, 5)]

        # Melt dataframe for visualization
        df_melted = df_filtered.melt(
            id_vars=["MAJOR_OCCUPATION_GROUP", "CATEGORY"],
            value_vars=selected_years,
            var_name="Year",
            value_name="Emigrants"
        )

        # Create grouped bar chart (faceted by employment category)
        fig_grouped = px.bar(
            df_melted,
            x="Year",
            y="Emigrants",
            color="MAJOR_OCCUPATION_GROUP",
            barmode="group",
            facet_col="CATEGORY",
            title="Comparison of Employed vs Unemployed Occupation Groups (1981–2020, every 5 years)"
        )

        fig_grouped.update_layout(
            height=600,
            legend_title="Occupation Group",
            xaxis_title="Year",
            yaxis_title="Number of Emigrants",
            bargap=0.15,
        )
        st.plotly_chart(fig_grouped, use_container_width=True)

    except Exception as e:
        st.error(f"Error cleaning or visualizing dataset: {e}")

# ---------- 2️⃣ SEX FILE ----------
def display_sex_data():
    st.header("🚻 Emigrant-1981-2020-Sex.xlsx")

    path = Path(__file__).parent / "Emigrant-1981-2020-Sex.xlsx"

    # --- STEP 1: Show RAW dataset ---
    st.subheader("📂 Raw Dataset Preview")

    try:
        raw_df = pd.read_excel(path, engine="openpyxl")
        raw_df = raw_df.astype(str)
        st.dataframe(raw_df.head(10), width="stretch")
        st.caption("👀 Raw data (first 10 rows) — notice unformatted headers and sex ratio format like '71M/100F'.")
    except Exception as e:
        st.error(f"Error loading raw dataset: {e}")
        return

    st.divider()

    # --- STEP 2: Cleaning Process Overview ---
    st.subheader("🧹 Cleaning Process Overview")
    st.write("""
    To prepare the dataset for analysis:
    1. Skipped extra header rows  
    2. Standardized column names  
    3. Removed blank rows  
    4. Converted numeric columns properly  
    5. Cleaned and normalized 'SEX_RATIO' values (e.g., '71M/100F' → 71 → 0.71 ratio)  
    """)

    st.divider()

    # --- STEP 3: Load & Clean Data ---
    st.subheader("✅ Cleaned Dataset Preview")

    try:
        df = (
            pd.read_excel(path, header=2, engine="openpyxl")
            .dropna(axis=1, how="all")
            .dropna(how="all")
        )

        expected_cols = ["YEAR", "MALE", "FEMALE", "TOTAL", "SEX_RATIO"]
        if len(df.columns) >= len(expected_cols):
            df = df.iloc[:, :len(expected_cols)]
            df.columns = expected_cols

        df = df[df["YEAR"].notna()]
        df["YEAR"] = df["YEAR"].astype(str).str.strip()

        # --- Clean SEX_RATIO column ---
        if "SEX_RATIO" in df.columns:
            df["SEX_RATIO"] = (
                df["SEX_RATIO"]
                .astype(str)
                .str.extract(r"(\d+)")
                .astype(float)
                / 100
            )
        else:
            df["SEX_RATIO"] = 0

        numeric_cols = [c for c in df.columns if c not in ["YEAR"]]
        df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors="coerce").fillna(0)

        df_full = df.copy()
        df_viz = df[~df["YEAR"].str.contains("TOTAL|Average", case=False, na=False)]

        # --- Show dataframe info ---
        st.dataframe(df_full.head(10), width="stretch")
        st.caption("✅ Cleaned dataset (first 10 rows) — ready for visualization.")

        st.divider()

        # --- STEP 4: Visualization ---
        st.subheader("📊 Population Pyramid: Male vs Female Emigrants (1981–2020)")

        # Prepare data
        df_pyramid = df_viz.copy()
        df_pyramid["MALE"] = -df_pyramid["MALE"]  # Negative for left side

        # Create population pyramid
        fig = go.Figure()

        fig.add_trace(go.Bar(
            y=df_pyramid["YEAR"],
            x=df_pyramid["MALE"],
            name="Male",
            orientation="h",
            marker_color="#3A7CA5",
            hovertemplate="Year %{y}<br>Male: %{x:,}"
        ))

        fig.add_trace(go.Bar(
            y=df_pyramid["YEAR"],
            x=df_pyramid["FEMALE"],
            name="Female",
            orientation="h",
            marker_color="#F75C03",
            hovertemplate="Year %{y}<br>Female: %{x:,}"
        ))

        # Update layout for pyramid
        fig.update_layout(
            barmode="overlay",
            title="Population Pyramid of Filipino Emigrants (1981–2020)",
            xaxis=dict(
                title="Number of Emigrants",
                tickvals=[-40000, -30000, -20000, -10000, 0, 10000, 20000, 30000, 40000],
                ticktext=["40k", "30k", "20k", "10k", "0", "10k", "20k", "30k", "40k"]
            ),
            yaxis=dict(
                title="Year",
                categoryorder="category ascending",
                tickmode="array",
                tickvals=df_pyramid["YEAR"][::5],  # Show every 5 years
            ),
            legend=dict(title="Sex", orientation="h", y=1.1, x=0.25),
            height=700,
            template="plotly_dark"
        )

        st.plotly_chart(fig, use_container_width=True)

        st.caption("""
        👫 This **population pyramid** compares male and female emigrants per year.  
        Negative values (left) represent **males**, while positive values (right) represent **females**.  
        You can easily observe gender balance changes across four decades of migration.
        """)

    except Exception as e:
        st.error(f"Error cleaning or visualizing dataset: {e}")

# ---------- 7️⃣ CIVIL STATUS FILE ----------
def display_civil_data():
    st.header("💍 Emigrant-1988-2020-CivilStatus.xlsx")

    path = Path(__file__).parent / "Emigrant-1988-2020-CivilStatus.xlsx"

    # --- STEP 1: Show RAW dataset ---
    st.subheader("📂 Raw Dataset Preview")

    try:
        raw_df = pd.read_excel(path, engine="openpyxl")
        raw_df = raw_df.astype(str)
        st.dataframe(raw_df.head(10), width="stretch")
        st.caption("👀 Raw data (first 10 rows) — unformatted headers and mixed value types.")
    except Exception as e:
        st.error(f"Error loading raw dataset: {e}")
        return

    st.divider()

    # --- STEP 2: Cleaning Process ---
    st.subheader("🧹 Cleaning Process Overview")
    st.write("""
    To prepare the dataset for analysis:
    1. Skipped unnecessary header rows  
    2. Standardized column names  
    3. Removed empty rows and columns  
    4. Converted numeric columns properly  
    5. Filtered only valid year rows (removed TOTAL/AVERAGE rows)
    """)

    st.divider()

    # --- STEP 3: Load & Clean Data ---
    st.subheader("✅ Cleaned Dataset Preview")

    try:
        df = (
            pd.read_excel(path, header=2, engine="openpyxl")
            .dropna(axis=1, how="all")
            .dropna(how="all")
        )

        expected_cols = [
            "YEAR", "Single", "Married", "Widower", "Separated",
            "Divorced", "Not_Reported", "TOTAL"
        ]
        if len(df.columns) >= len(expected_cols):
            df = df.iloc[:, :len(expected_cols)]
            df.columns = expected_cols

        df = df[df["YEAR"].notna()]
        df["YEAR"] = df["YEAR"].astype(str).str.strip()

        # Remove TOTAL or Average rows
        df_viz = df[~df["YEAR"].str.contains("TOTAL|Average", case=False, na=False)]

        numeric_cols = [c for c in df.columns if c != "YEAR"]
        df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors="coerce").fillna(0).astype(int)

        show_df_info(df, "Cleaned Civil Status dataset")

        st.divider()

        # --- STEP 4: Visualization ---
        st.subheader("📊 Horizontal Stacked Bar Chart: Civil Status Distribution (1988–2020)")

        import plotly.express as px

        df_long = df_viz.melt(
            id_vars="YEAR",
            value_vars=["Single", "Married", "Widower", "Separated", "Divorced", "Not_Reported"],
            var_name="Civil Status",
            value_name="Emigrants"
        )

        color_map = {
            "Single": "#C9CBA3",
            "Married": "#FFE1A8",
            "Widower": "#E26D5C",
            "Separated": "#723D46",
            "Divorced": "#472D30",
            "Not_Reported": "#A9A9A9"
        }

        fig = px.bar(
            df_long,
            y="YEAR",
            x="Emigrants",
            color="Civil Status",
            color_discrete_map=color_map,
            title="Horizontal Stacked Bar Chart of Filipino Emigrants by Civil Status (1988–2020)",
            labels={"Emigrants": "Number of Emigrants", "YEAR": "Year"},
            orientation="h"
        )

        fig.update_layout(
            barmode="stack",
            height=900,
            xaxis_title="Number of Emigrants",
            yaxis_title="Year",
            legend_title="Civil Status",
            hovermode="y unified",
            template="plotly_dark",
        )

        st.plotly_chart(fig, use_container_width=True)

        st.caption("""
        📊 This **horizontal stacked bar chart** shows the distribution of emigrants by civil status from 1988–2020.
        Each bar represents a year, divided into civil status categories.  
        Married individuals dominate throughout, while singles and widowers vary slightly over time.  
        The sharp drop in 2020 again reflects **pandemic-related migration slowdowns**.
        """)

        st.divider()

    except Exception as e:
        st.error(f"Error cleaning or visualizing dataset: {e}")

# ---------- 8️⃣ EDUCATION FILE ----------
def display_educ_data():
    st.header("🎓 Emigrant-1988-2020-Educ.xlsx")

    path = Path(__file__).parent / "Emigrant-1988-2020-Educ.xlsx"

    # --- STEP 1: Raw Dataset Preview ---
    st.subheader("📂 Raw Dataset Preview")

    try:
        raw_df = pd.read_excel(path, engine="openpyxl")
        raw_df = raw_df.astype(str)
        st.dataframe(raw_df.head(10), width="stretch")
        st.caption("👀 Raw data (first 10 rows) — unformatted headers and non-numeric cells present.")
    except Exception as e:
        st.error(f"Error loading raw dataset: {e}")
        return

    st.divider()

    # --- STEP 2: Cleaning Process Overview ---
    st.subheader("🧹 Cleaning Process Overview")
    st.write("""
    To prepare the dataset for analysis:
    1. Skipped unnecessary header rows  
    2. Standardized column names  
    3. Removed empty rows/columns  
    4. Converted numeric values properly  
    5. Removed TOTAL and non-educational rows  
    """)

    st.divider()

    # --- STEP 3: Cleaned Dataset Preview ---
    st.subheader("✅ Cleaned Dataset Preview")

    try:
        df = pd.read_excel(path, header=2, engine="openpyxl").dropna(axis=1, how="all").dropna(how="all")

        expected_cols = ["EDUCATIONAL_ATTAINMENT", *map(str, range(1988, 2021)), "TOTAL"]
        if len(df.columns) >= len(expected_cols):
            df = df.iloc[:, :len(expected_cols)]
            df.columns = expected_cols

        df = df[df["EDUCATIONAL_ATTAINMENT"].notna()]
        df["EDUCATIONAL_ATTAINMENT"] = df["EDUCATIONAL_ATTAINMENT"].astype(str).str.strip()

        # Remove TOTAL and empty rows
        df_viz = df[~df["EDUCATIONAL_ATTAINMENT"].str.contains("TOTAL", case=False, na=False)]
        df_viz = df_viz[df_viz["EDUCATIONAL_ATTAINMENT"].str.len() > 1]

        numeric_cols = [c for c in df_viz.columns if c != "EDUCATIONAL_ATTAINMENT"]
        df_viz[numeric_cols] = (
            df_viz[numeric_cols].apply(pd.to_numeric, errors="coerce").fillna(0).astype(int)
        )

        show_df_info(df_viz, "Cleaned Education dataset ready for visualization")

        st.divider()

        # --- STEP 4: Visualization ---
        st.subheader("📊 Heatmap: Educational Attainment Trends (1988–2020)")

        # Melt for visualization
        df_melted = df_viz.melt(
            id_vars="EDUCATIONAL_ATTAINMENT",
            var_name="Year",
            value_name="Emigrants"
        )

        # Ensure correct year order
        df_melted["Year"] = pd.Categorical(
            df_melted["Year"],
            categories=[str(y) for y in range(1988, 2021)],
            ordered=True
        )

        # Pivot safely to avoid duplicates — explicitly set observed=False to silence FutureWarning
        df_pivot = df_melted.pivot_table(
            index="EDUCATIONAL_ATTAINMENT",
            columns="Year",
            values="Emigrants",
            aggfunc="sum",
            observed=False  # ✅ prevents pandas FutureWarning
        )

        # Plotly heatmap
        fig = px.imshow(
            df_pivot,
            color_continuous_scale="YlGnBu",
            aspect="auto",
            title="Heatmap of Filipino Emigrants by Educational Attainment (1988–2020)",
            labels=dict(x="Year", y="Educational Attainment", color="Number of Emigrants")
        )

        fig.update_layout(
            height=650,
            template="plotly_dark",
            xaxis_title="Year",
            yaxis_title="Educational Attainment",
            coloraxis_colorbar_title="Emigrants",
            margin=dict(l=80, r=30, t=100, b=60)
        )

        # ✅ Modern Streamlit 2025+ syntax: all inside `config`
        st.plotly_chart(
            fig,
            config={
                "displayModeBar": False,
                "width": "stretch"  # replaces old width argument
            }
        )

        st.caption("""
        🌡️ This **heatmap** visualizes the number of emigrants by educational level and year.
        Darker shades represent higher counts, showing which education levels dominated over time.
        """)

        st.divider()

    except Exception as e:
        st.error(f"Error cleaning or visualizing dataset: {e}")

# ---------- 9️⃣ PLACE OF ORIGIN FILE ----------
def display_place_data():
    st.header("🧭 Emigrant-1988-2020-PlaceOfOrigin.xlsx")

    path = Path(__file__).parent / "Emigrant-1988-2020-PlaceOfOrigin.xlsx"

    try:
        excel_file = pd.ExcelFile(path)
        sheet_names = excel_file.sheet_names
    except Exception as e:
        st.error(f"Error loading Excel file: {e}")
        return

    # ------- Clean each sheet -------
    def clean_sheet(sheet_name):
        try:
            df = pd.read_excel(path, sheet_name=sheet_name, header=None, engine="openpyxl")
            header_row = 2
            df.columns = (
                df.iloc[header_row]
                .astype(str)
                .str.strip()
                .str.replace(r"\.0$", "", regex=True)
            )

            df = df.drop(index=list(range(0, header_row + 1)))
            df = df.loc[:, ~df.columns.astype(str).str.contains("^Unnamed")]
            df = df.loc[:, df.columns.astype(str).str.strip() != ""]
            df = df.reset_index(drop=True)

            df.columns = (
                df.columns.str.replace(r"[\*\%\(\)\.]", "", regex=True)
                .str.replace(" ", "_")
                .str.strip()
            )

            first_col = df.columns[0]
            df[first_col] = df[first_col].astype(str).str.strip()
            df = df[df[first_col].notna()]
            df = df[~df[first_col].astype(str).str.match(r"(?i)^nan$")]

            if sheet_name != "REGION":
                df = df[~df[first_col].astype(str).str.match(r"(?i)^Region")]

            for col in df.columns:
                if col != first_col:
                    df[col] = pd.to_numeric(df[col], errors="coerce")

            df = df.dropna(axis=1, how="all")
            df = df[df.drop(columns=[first_col]).fillna(0).sum(axis=1) != 0]

            numeric_cols = df.select_dtypes(include=["number"]).columns
            df[numeric_cols] = df[numeric_cols].fillna(0).astype(int)

            df.index = range(len(df))
            df.index.name = None

            return df

        except Exception as e:
            st.error(f"Error cleaning sheet '{sheet_name}': {e}")
            return pd.DataFrame()

    # ------- Tabs for each sheet -------
    tabs = st.tabs([f"📍 {name}" for name in sheet_names])

    for tab, name in zip(tabs, sheet_names):
        with tab:
            st.subheader(f"📘 {name} Dataset")

            # STEP 1: Raw Dataset
            st.subheader("📂 Raw Dataset Preview")
            try:
                raw_df = pd.read_excel(path, sheet_name=name, engine="openpyxl")
                raw_df = raw_df.astype(str)
                st.dataframe(raw_df.head(10), width="stretch")
                st.caption("👀 Raw data (first 10 rows).")
            except Exception as e:
                st.error(f"Error loading raw sheet '{name}': {e}")
                continue

            st.divider()

            # STEP 2: Cleaned Dataset
            st.subheader("✅ Cleaned Dataset Preview")
            df = clean_sheet(name)
            if df.empty:
                st.warning(f"⚠️ No valid data found for {name}")
                continue
            st.dataframe(df.head(10), width="stretch")
            first_col = df.columns[0]
            numeric_cols = df.select_dtypes(include="number").columns

            st.divider()
            st.subheader("📊 Visualization")

            config = {"displaylogo": False, "responsive": True}

            # --- REGION: Line Chart ---
            if name.upper() == "REGION":
                st.markdown("### 📈 Regional Migration Trends (1988–2020)")

                # Remove TOTAL / NOT REPORTED / NO RESPONSE
                df[first_col] = df[first_col].astype(str).str.strip()
                df = df[
                    ~df[first_col].str.match(r"(?i)^(total|totals|not\s*reported|no\s*response)$", na=False)
                ]

                # Melt for line chart
                df_melted = df.melt(id_vars=first_col, var_name="Year", value_name="Emigrants")
                df_melted["Year"] = pd.to_numeric(df_melted["Year"], errors="coerce")
                df_melted = df_melted.dropna(subset=["Year"])

                fig = px.line(
                    df_melted,
                    x="Year",
                    y="Emigrants",
                    color=first_col,
                    markers=True,
                    title="Regional Migration Trends Over Time",
                    labels={"Emigrants": "Number of Emigrants", "Year": "Year", first_col: "Region"},
                )
                fig.update_traces(line=dict(width=2))
                fig.update_layout(width=900, height=500)
                if not df_melted["Emigrants"].isna().all():
                    fig.update_yaxes(range=[0, df_melted["Emigrants"].max() * 1.1])
                st.plotly_chart(fig, config=config, use_container_width=True)
                st.caption("📈 Showing how emigration trends vary across regions from 1988–2020 (Total excluded).")

            # --- PROVINCE: Horizontal Bar Chart ---
            elif name.upper() == "PROVINCE":
                st.markdown("### 🏞️ Top Provinces by Total Emigrants")
                top_n = st.slider("Select number of top provinces:", 5, 30, 15)

                # Remove total / not reported rows
                df = df[
                    ~df[first_col].str.match(r"(?i)^(total|totals|not\s*reported|no\s*response)$", na=False)
                ]

                df["Total"] = df[numeric_cols].sum(axis=1)
                top_df = df.nlargest(top_n, "Total")

                fig = px.bar(
                    top_df,
                    x="Total",
                    y=first_col,
                    orientation="h",
                    color="Total",
                    color_continuous_scale="Viridis",
                    title=f"Top {top_n} Provinces by Total Emigrants (1988–2020)",
                    labels={first_col: "Province", "Total": "Total Emigrants"},
                )
                fig.update_layout(width=900, height=600, yaxis={'categoryorder': 'total ascending'})
                st.plotly_chart(fig, config=config, use_container_width=True)
                st.caption(f"📊 Showing top {top_n} provinces by total emigrants (1988–2020).")

            # --- MUNICIPALITY: Pie Chart ---
            elif name.upper() == "MUNICIPALITY":
                st.markdown("### 🥧 Municipality Emigrant Distribution")
                top_n = st.slider("Select number of top municipalities:", 5, 30, 15)

                # Remove total / grand total / not reported rows
                df = df[
                    ~df[first_col].str.match(r"(?i)^(total|grand\s*total|totals|not\s*reported|no\s*response)$", na=False)
                ]

                df["Total"] = df[numeric_cols].sum(axis=1)
                top_df = df.nlargest(top_n, "Total")

                fig = px.pie(
                    top_df,
                    values="Total",
                    names=first_col,
                    title=f"Top {top_n} Municipalities by Total Emigrants (1988–2020)",
                    hole=0.3,
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                fig.update_layout(width=800, height=600)
                st.plotly_chart(fig, config=config, use_container_width=True)
                st.caption(f"🥧 Pie chart showing top {top_n} municipalities by total emigrants (1988–2020).")


# ---------- MAIN ----------
def main():
    st.sidebar.title("📂 Filipino Emigrant Datasets")
    st.sidebar.info("Navigate between datasets using the tabs below.")

    tabs = st.tabs([
        "📖 Overview & Story",
        "🧒 Age",
        "🌍 All Countries",
        "🏆 Major Countries",
        "💼 Occupation",
        "🚻 Sex",
        "💍 Civil Status",
        "🎓 Education",
        "🧭 Place of Origin"
    ])

    with tabs[0]:
        display_story_intro()

    with tabs[1]:
        display_age_data()

    with tabs[2]:
        display_country_data()

    with tabs[3]:
        display_major_country_data()

    with tabs[4]:
        display_occu_data()

    with tabs[5]:
        display_sex_data()

    with tabs[6]:
        display_civil_data()

    with tabs[7]:
        display_educ_data()

    with tabs[8]:
        display_place_data()  # this one has its own subtabs already

if __name__ == "__main__":
    main()
