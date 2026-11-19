import os
import duckdb
from datetime import datetime, timezone
from google import genai
from google.genai import types
import json

class AIPipelineAnalyst:
    """
    An Object-Oriented GenAI Agent that evaluates 5-day meteorological trajectories
    (Temperature, Barometric Pressure, and Humidity), applies multi-model failover routing,
    and persists intelligence back into DuckDB.
    """
    def __init__(self, db_path="weather_data.duckdb"):
        self.db_path = db_path
        self.api_key = os.environ.get("GEMINI_API_KEY")
        self.report_file = "LATEST_METEOROLOGY_REPORT.md"

        if not self.api_key:
            raise ValueError("System Guard Alert: GEMINI_API_KEY environment variable is missing.")

        self.client = genai.Client(api_key=self.api_key)

        # Updated system prompt to correlate temperature, pressure drops, and humidity
        self.system_instruction = (
            "You are a senior wilderness safety meteorologist analyzing 5-day weather trajectories "
            "across global tracking nodes (Toronto, Los Angeles, London, Sydney, Tokyo). "
            "Compare the earliest readings in the 5-day window against the most recent readings for each city. "
            "Correlate temperature swings, barometric pressure trends (e.g., falling pressure signaling storm fronts), "
            "and relative humidity levels to identify emerging outdoor safety hazards. "
            "Format your response as a concise executive bulletin with one short bullet point per city. "
            "Keep the total response under 200 words."
        )

    def generate_daily_report(self):
        print("\n[AI Analyst] Connecting to DuckDB warehouse for 5-day telemetry extraction...")
        conn = duckdb.connect(self.db_path)

        try:
            # ==========================================
            # TRY BLOCK 1: FRESHNESS GATE & 5-DAY EXTRACTION
            # ==========================================
            latest_date_row = conn.execute("""
                SELECT MAX(reading_date) 
                FROM main_weather_data.fct_weather_summary
                WHERE reading_date >= CURRENT_DATE - INTERVAL '1' DAY;
            """).fetchone()

            if not latest_date_row or latest_date_row[0] is None:
                print("[AI Analyst] Freshness SLA failed: No data within the last 24 hours. Skipping AI analysis.")
                return

            # Pull Temperature, Barometric Pressure, and Relative Humidity across the 5-day window
            query_results = conn.execute("""
                SELECT 
                    city_node, 
                    reading_date, 
                    avg_temperature_celsius, 
                    max_temperature_celsius, 
                    min_temperature_celsius,                    
                    avg_barometric_pressure_hpa,
                    avg_humidity_percentage,
                FROM main_weather_data.fct_weather_summary
                WHERE reading_date >= CURRENT_DATE - INTERVAL '5' DAY
                ORDER BY city_node ASC, reading_date ASC;
            """).fetchall()

            if not query_results:
                print("[AI Analyst] No records found in 5-day window. Skipping AI analysis.")
                return

            # Format all 5 metrics into a structured chronological payload for Gemini
            payload_lines = ["5-Day Global Weather Telemetry (Chronological by City):"]
            for row in query_results:
                city, r_date, avg_t, max_t, min_t, avg_p, avg_h = row
                payload_lines.append(
                    f"- {city} | {r_date}: Temp Avg {avg_t:.1f}°C (Min {min_t:.1f}°C / Max {max_t:.1f}°C) | "
                    f"Pressure {avg_p:.1f} hPa | Humidity {avg_h:.0f}%"
                )
            data_payload = "\n".join(payload_lines)

            # ==========================================
            # TRY BLOCK 2: AI INFERENCE (STRUCTURED JSON)
            # ==========================================
            json_instruction = (
                "You are a senior wilderness safety meteorologist analyzing 5-day weather trajectories. "
                "Compare the earliest readings in the 5-day window against the most recent readings for each city. "
                "Correlate temperature swings, barometric pressure trends, and relative humidity levels to identify outdoor safety hazards. "
                "Return ONLY a valid JSON object where each key is the exact city node string (e.g., 'Toronto,CA', 'Los Angeles,US', 'London,GB', 'Sydney,AU', 'Tokyo,JP') "
                "and each value is a concise 1-to-2 sentence safety briefing for that city. Do not wrap the JSON in markdown code blocks."
            )

            candidate_models = [
                "gemini-3.5-flash-lite",
                "gemini-3.5-flash",
                "gemini-3.8-flash"
            ]

            city_insights_dict = None
            successful_model = "FALLBACK_ADVISORY"

            for model_name in candidate_models:
                try:
                    print(f"[AI Analyst] Requesting structured JSON synthesis from {model_name}...")
                    response = self.client.models.generate_content(
                        model=model_name,
                        contents=data_payload,
                        config=types.GenerateContentConfig(
                            system_instruction=json_instruction,
                            response_mime_type="application/json",
                            temperature=0.3
                        )
                    )
                    city_insights_dict = json.loads(response.text.strip())
                    successful_model = model_name
                    print(f"[AI Analyst] Structured JSON synthesis complete via {model_name}.")
                    break
                except Exception as api_err:
                    print(f"[⚠️ AI WARNING] {model_name} unavailable ({api_err}). Routing to next model...")

            if not city_insights_dict:
                print("[AI SYSTEM WARNING] All Gemini models busy. Writing fallback dictionary.")
                fallback_msg = "Automated meteorological commentary is temporarily unavailable due to high upstream API demand."
                city_insights_dict = {
                    "Toronto,CA": fallback_msg,
                    "Los Angeles,US": fallback_msg,
                    "London,GB": fallback_msg,
                    "Sydney,AU": fallback_msg,
                    "Tokyo,JP": fallback_msg
                }

            # ==========================================
            # TRY BLOCK 3: PERSIST TO DUCKDB & MARKDOWN
            # ==========================================
            conn.execute("""
                CREATE TABLE IF NOT EXISTS main_weather_data.ai_weather_insights (
                    generated_at TIMESTAMP,
                    model_used VARCHAR,
                    trend_analysis VARCHAR
                );
            """)

            # Store the JSON string in DuckDB for Streamlit lookup
            conn.execute("""
                INSERT INTO main_weather_data.ai_weather_insights (generated_at, model_used, trend_analysis)
                VALUES (CURRENT_TIMESTAMP, ?, ?);
            """, (successful_model, json.dumps(city_insights_dict)))
            print(f"[AI Analyst] Structured JSON insights persisted to DuckDB (Model: {successful_model}).")

            # Format cleanly as bullet points for the GitHub Markdown ledger
            formatted_bullets = "\n".join([f"* **{city}:** {note}" for city, note in city_insights_dict.items()])
            timestamp_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            new_entry = (
                f"### 🌐 5-Day Trajectory Report — {timestamp_str}\n"
                f"*Engine: `{successful_model}`*\n\n"
                f"{formatted_bullets}\n\n---\n\n"
            )

            existing_content = ""
            if os.path.exists(self.report_file):
                with open(self.report_file, "r", encoding="utf-8") as f:
                    existing_content = f.read()

            with open(self.report_file, "w", encoding="utf-8") as f:
                f.write(new_entry + existing_content)
            print(f"[AI Analyst] Prepended formatted bullets to {self.report_file}.")
   

        except Exception as e:
            print(f"[AI Analyst] CRITICAL PIPELINE ERROR: {e}")
            raise
        finally:
            conn.close()

if __name__ == "__main__":
    analyst = AIPipelineAnalyst()
    analyst.generate_daily_report()