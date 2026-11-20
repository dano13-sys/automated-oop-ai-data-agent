# automated-oop-ai-data-agent
# 🗺️ Global Weather Intelligence & AI Data Platform

🚀 **[Launch Live Interactive Streamlit Dashboard](https://streamlit.app)**

An automated, end-to-end data engineering and GenAI analytics platform that ingests live global weather telemetry across five international nodes, transforms metrics using **dbt** and **DuckDB**, synthesizes multi-day meteorological safety briefings with **Google Gemini**, and publishes real-time interactive visualizations to **Streamlit Community Cloud**.

---

### 🏗️ System Architecture

```text
[OpenWeatherMap API] ──► [Python OOP Ingestor] ──► [DuckDB Warehouse] ──► [dbt Data Marts]
                                                                                 │
[Executive Dashboard] ◄── [Streamlit Community Cloud] ◄── [GitHub Repo] ◄── [Gemini AI Analyst]
```

* **Ingestion Layer (`ingestor.py`):** Object-oriented Python pipeline pulling live temperature, barometric pressure, and humidity metrics for Toronto, Los Angeles, London, Sydney, and Tokyo.
* **Transformation Layer (`dbt` + `DuckDB`):** Materializes clean analytical marts (`fct_weather_summary`) with automated 24-hour data freshness guards.
* **GenAI Trajectory Layer (`analyst.py`):** Evaluates 5-day multi-metric weather trajectories using Google Gemini (`gemini-3.5-flash-lite` with automated model failover) and persists structured JSON briefings directly back into DuckDB.
* **Orchestration (`GitHub Actions`):** Serverless CI/CD pipeline (`run_pipeline.yml`) executing hourly to refresh data, compile models, and commit updated warehouse snapshots.
* **Presentation Layer (`dashboard.py`):** Interactive Streamlit & Plotly dashboard synced directly with GitHub for zero-maintenance public access.
