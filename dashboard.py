import os
import duckdb
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import json

# 1. PAGE CONFIGURATION & THEME INJECTION
st.set_page_config(
    page_title="Weather Intelligence Center",
    page_icon="⚡",
    layout="wide"
)

# Premium typography, clean containment boxes, and responsive grid padding
st.markdown("""
    <style>
        .block-container {padding-top: 1.5rem; padding-bottom: 1.5rem;}
        h1 {font-weight: 800; letter-spacing: -0.04em; color: #0F172A;}
        .metric-card {
            background: #F8FAFC; 
            padding: 1.25rem; 
            border-radius: 0.5rem; 
            border: 1px solid #E2E8F0;
            box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        }
    </style>
""", unsafe_allow_html=True)

st.title("⚡ Operational Weather Intelligence Center")
st.markdown("Global sensor telemetry analytics and automated safety metrics execution platform.")
st.markdown("---")

# 2. LIVE DATA EXTRACTION LAYER (DuckDB Production Engine)
DB_PATH = "weather_data.duckdb"

if not os.path.exists(DB_PATH):
    st.error(f"❌ Critical System Error: Database file `{DB_PATH}` not found in the root execution workspace.")
    df = pd.DataFrame()  # Fallback to prevent crash
else:
    conn = duckdb.connect(DB_PATH)
    try:
        # LIVE SQL: Grabs the last 5 active distinct calendar days in the system,
        # aggregating rows to completely flatten and neutralize any raw ingestion duplicates.
        df = conn.execute("""
            WITH max_5_days AS (
                SELECT DISTINCT CAST(reading_date AS DATE) as unique_date
                FROM main_weather_data.fct_weather_summary
                ORDER BY unique_date DESC
                LIMIT 5
            )
            SELECT 
                city_node, 
                CAST(reading_date AS DATE) as reading_date,
                AVG(avg_temperature_celsius) as avg_temperature_celsius, 
                MAX(max_temperature_celsius) as max_temperature_celsius, 
                MIN(min_temperature_celsius) as min_temperature_celsius,
                AVG(avg_barometric_pressure_hpa) as avg_barometric_pressure_hpa,
                AVG(avg_humidity_percentage) as avg_humidity_percentage
            FROM main_weather_data.fct_weather_summary
            WHERE CAST(reading_date AS DATE) IN (SELECT unique_date FROM max_5_days)
            GROUP BY city_node, CAST(reading_date AS DATE)
            ORDER BY reading_date ASC, city_node ASC;
        """).df()
       
        # Clean up technical column strings into human-readable chart display headers
        df = df.rename(columns={
            "reading_date": "Date",
            "min_temperature_celsius": "Min Temp",
            "avg_temperature_celsius": "Avg Temp",
            "max_temperature_celsius": "Max Temp",
            "avg_barometric_pressure_hpa": "Barometric Pressure (hPa)",
            "avg_humidity_percentage": "Relative Humidity (%)"
        })

        df['city_node'] = df['city_node'].str.replace(',', ', ')

    except Exception as query_err:
        st.error(f"❌ Database Query Compilation Failure: {query_err}")
        df = pd.DataFrame()
    finally:
        conn.close()

# 3. INTERACTIVE RENDERING LAYER
if not df.empty:
    # Format the date explicitly into a clean text string for the timeline axis
    df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%b %d')

    # NAVIGATION: Feed the sidebar selector with unique nodes pulled straight from the warehouse
    st.sidebar.header("🎯 Node Configuration")
    selected_city = st.sidebar.selectbox(
        "Select Active Tracking Node:",
        options=df["city_node"].unique()
    )

    # Slice the dataframe down to the single user-selected focus node
    city_df = df[df["city_node"] == selected_city].reset_index(drop=True)

    # --- TIER 1: LIVE EXECUTIVE METRIC TILES ---
    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown(f"""
            <div class="metric-card">
                <small style='color: #64748B; font-weight: 600;'>CURRENT ACTIVE FOCUS</small>
                <h2 style='margin:0; color: #0284c7;'>📍 {selected_city}</h2>
            </div>
        """, unsafe_allow_html=True)
    with m2:
        mean_temp = city_df['Avg Temp'].mean()
        st.markdown(f"""
            <div class="metric-card">
                <small style='color: #64748B; font-weight: 600;'>5-DAY THERMAL BASELINE</small>
                <h2 style='margin:0; color: #0F172A;'>🌡️ {mean_temp:.1f} °C</h2>
            </div>
        """, unsafe_allow_html=True)
    with m3:
        latest_hum = city_df['Relative Humidity (%)'].iloc[-1]
        status_text = "Optimal Comfort" if 30 <= latest_hum <= 65 else "High Moisture Saturation"
        status_color = "#10B981" if "Optimal" in status_text else "#F59E0B"
        st.markdown(f"""
            <div class="metric-card">
                <small style='color: #64748B; font-weight: 600;'>ATMOSPHERIC COMFORT STATUS</small>
                <h2 style='margin:0; color: {status_color};'>💧 {status_text}</h2>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    # --- CITY-SPECIFIC AI METEOROLOGICAL BRIEFING ---
    with duckdb.connect(DB_PATH) as conn:
        try:
            latest_insight = conn.execute("""
                SELECT generated_at, model_used, trend_analysis 
                FROM main_weather_data.ai_weather_insights 
                ORDER BY generated_at DESC 
                LIMIT 1;
            """).fetchone()

            if latest_insight:
                gen_time, model_tag, raw_json_str = latest_insight
                insights_map = json.loads(raw_json_str)
                
                # Match selected city whether formatted with a comma-space ("Toronto, CA") or raw ("Toronto,CA")
                raw_city_key = selected_city.replace(", ", ",")
                city_briefing = insights_map.get(raw_city_key) or insights_map.get(selected_city)

                if city_briefing:
                    st.info(f"**🧠 AI Trajectory Briefing ({selected_city}):** {city_briefing}  \n*Synthesized {str(gen_time)[:16]} UTC via `{model_tag}`*")
        except Exception:
            pass  # Silently skip if table isn't populated yet

        # Existing Telemetry Section Header sits right below the AI briefing
        st.markdown("### System Telemetry Horizons (Last 5 Days)")

    # --- TIER 2: VARIABLE COLUMNS GRID ---
    chart_col1, chart_col2 = st.columns(2)

    # Initialize chart objects up front so static analysis and downstream rendering
    # consistently see these variables in scope before they are populated.
    fig_left = go.Figure()
    fig_right = go.Figure()

    with chart_col1:
        st.markdown("#### Thermal Envelope & Barometric Trend")
        
                
        # 1. Temperature Envelope Shading Range
        fig_left.add_trace(go.Scatter(
            x=pd.concat([city_df['Date'], city_df['Date'].iloc[::-1]]),
            y=pd.concat([city_df['Max Temp'], city_df['Min Temp'].iloc[::-1]]),
            fill='toself',
            fillcolor='rgba(14, 165, 233, 0.06)', 
            line=dict(color='rgba(255,255,255,0)'),
            hoverinfo="skip",
            name="Temperature Range",
            yaxis="y1"
        ))
        
        # 2. Solid Main Average Core Line
        fig_left.add_trace(go.Scatter(
            x=city_df['Date'],
            y=city_df['Avg Temp'],
            mode='lines+markers',
            line=dict(color='#0ea5e9', width=3.5),
            marker=dict(size=7, color='#0284c7'),
            name="Mean Temp (°C)",
            yaxis="y1"
        ))
        
        # 3. Secondary Dotted Line: Barometric Pressure
        fig_left.add_trace(go.Scatter(
            x=city_df['Date'],
            y=city_df['Barometric Pressure (hPa)'],
            mode='lines+markers',
            line=dict(color='#64748B', width=2, dash='dot'),
            marker=dict(size=6, symbol="diamond", color='#475569'),
            name="Pressure (hPa)",
            yaxis="y2"
        ))
        
        fig_left.update_layout(
           template="plotly_white",
           height=380,                        # Forces identical pixel height
           hovermode="x unified",
           xaxis_title=None,
           margin=dict(l=10, r=10, t=50, b=30), # Changed t=10 to t=50 to align with fig_right
           legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
           yaxis1=dict(
            title=dict(text="Temperature Metrics (°C)", font=dict(color="#0284c7")),
            gridcolor="#F1F5F9", 
            fixedrange=True,
            tickfont=dict(color="#0284c7")
        ),
        yaxis2=dict(
            title=dict(text="Barometric Pressure (hPa)", font=dict(color="#475569")),
            fixedrange=True,
            overlaying="y", 
            side="right",
            tickfont=dict(color="#475569"),
            gridcolor="rgba(0,0,0,0)"
        ),
        xaxis=dict(gridcolor="#F1F5F9", fixedrange=True)
        )
        
        st.plotly_chart(fig_left, use_container_width=True, config={'displayModeBar': False})

    with chart_col2:
        st.markdown("#### Atmospheric Moisture Timeline")
        
        fig_right = px.area(
            city_df,
            x="Date",
            y="Relative Humidity (%)",
            markers=True,
            color_discrete_sequence=["#10B981"],
            labels={"Relative Humidity (%)": "Humidity (%)"}
        )
        
        fig_right.update_traces(
            fillcolor="rgba(16, 185, 129, 0.08)", 
            line=dict(width=3)
        )
        
        fig_right.update_layout(
            template="plotly_white",    
            height=380,                        # Forces identical pixel height
            xaxis_title=None,                  # Removes the redundant "Date" label
            margin=dict(l=10, r=10, t=50, b=30) # Matches fig_left's exact top/bottom margins            
        )
        
        st.plotly_chart(fig_right, use_container_width=True, config={'displayModeBar': False})

    st.markdown("<br>", unsafe_allow_html=True)

    # --- TIER 3: CONSOLIDATED RAW ACCOUNTABILITY LEDGER ---
    with st.expander("🔎 View Structured Ingestion Ledger Data", expanded=False):
        # Format numbers to look clean in the grid
        grid_df = city_df.copy()
        grid_df['Avg Temp'] = grid_df['Avg Temp'].map('{:,.1f}°C'.format)
        grid_df['Min Temp'] = grid_df['Min Temp'].map('{:,.1f}°C'.format)
        grid_df['Max Temp'] = grid_df['Max Temp'].map('{:,.1f}°C'.format)
        grid_df['Barometric Pressure (hPa)'] = grid_df['Barometric Pressure (hPa)'].map('{:,.1f} hPa'.format)
        grid_df['Relative Humidity (%)'] = grid_df['Relative Humidity (%)'].map('{}%'.format)
        
        st.dataframe(
            grid_df.rename(columns={"city_node": "Node Location"}), 
            use_container_width=True, 
            hide_index=True
        )

    # --- TIER 4: GENAI 5-DAY TRAJECTORY BRIEFING ---
        st.markdown("---")
        st.subheader("🧠 AI Multi-Day Meteorological Briefing")
        
        with duckdb.connect(DB_PATH) as conn:
            try:
                latest_insight = conn.execute("""
                    SELECT generated_at, model_used, trend_analysis 
                    FROM main_weather_data.ai_weather_insights 
                    ORDER BY generated_at DESC 
                    LIMIT 1;
                """).fetchone()
                
                if latest_insight:
                    gen_time, model_tag, analysis_body = latest_insight
                    st.caption(f"Last Synthesized: {str(gen_time)[:16]} UTC | Engine: `{model_tag}`")
                    st.info(analysis_body)
                else:
                    st.caption("No AI trend briefings generated yet. Run analyst.py to populate.")
            except Exception as e:
                st.caption(f"AI insights table not yet initialized: {e}")

else:
    st.warning("⚠️ **Data Inaccessible:** The database query returned an empty set. Check that your upstream dbt pipeline has executed successfully.")