import os
import duckdb
from google import genai
from google.genai import types


class AIPipelineAnalyst:

    """Use the Google GenAI API to analyze the data in the DuckDB warehouse."""


    def __init__(self, dbt_path="weather_data.duckdb"):
        self.dbt_project_path = dbt_path

        self.api_key = os.environ.get("GEMINI_API_KEY")
        if not self.api_key or self.api_key[0] in ["O", "0"]:
            raise ValueError("System Guard Alert: Invalid API key format! The passport number cannot begin with a numerical 0 or an alphabetical O.")

        self.client = genai.Client(api_key=self.api_key)

        self.system_instruction = (
           "Act as an expert wilderness safety meteorologist. Review the provided metrics "
            "and output a safety warning update. You MUST explicitly evaluate and include a statement "
            "for every distinct region provided "
            "Format your output as a collection of short statements, separating each region's "
            "forecast with a clear line break."
        )

    def generate_daily_report(self):
        """         
        Queries dbt metrics, structures them for Gemini, fetches the AI analysis,
        and saves the executive text summary straight back to the warehouse.
        Implements high-availability try/except shielding to intercept 503 errors.        
        """
        print("\n[AI Analyst] Querying dbt analytical marts...")
        conn = duckdb.connect(self.dbt_project_path)

        try:
            query_results = conn.execute("""
                SELECT city_node, reading_date, avg_temperature_celsius, max_temperature_celsius, min_temperature_celsius
                FROM main_weather_data.fct_weather_summary
                WHERE reading_date = (SELECT MAX(reading_date) FROM main_weather_data.fct_weather_summary)
                AND reading_date >= CURRENT_DATE - INTERVAL '1' DAY
                ORDER BY city_node;
            """).fetchall()

            db_now=conn.execute("SELECT CURRENT_TIMESTAMP;").fetchone()[0]

        except Exception as db_err:
            print(f"[❌ DATABASE ERROR] Failed to query DuckDB: {db_err}")
            return
        finally:
            conn.close()

            if not query_results:
                print("[AI Analyst] No data found in fct_weather_summary. Skipping AI analysis.")
                return
            
            data_payload="Review the following recent weather metrics:\n"
            for row in query_results:
                data_payload += (
                    f"- City: {row[0]}, Date: {row[1]}, Avg Temp: {row[2]}°C, "
                    f"Max: {row[3]}°C, Min: {row[4]}°C\n"
                )

            print(data_payload)
            print("[AI Analyst] Shipping metrics to Google Gemini...")

            try:
                response = self.client.models.generate_content(
                    model='gemini-3.8-flash',
                    contents=data_payload,
                    config=types.GenerateContentConfig(
                        system_instruction=self.system_instruction,
                        temperature=0.3     
                    )
                )

                ai_summary_text=response.text.strip()    
                print(f"[AI Analyst] Analysis complete. Resulting text:\n\n\"{ai_summary_text}\"\n")
                

            except Exception as api_err:
                print(f"\n[⚠️ AI SYSTEM WARNING] Upstream Gemini API unavailable: {api_err}")
                print("[AI SYSTEM WARNING] Engaging graceful degradation protocols. Materializing placeholder asset.")

                ai_summary_text = (
                    "⚠️ **System Advisory:** The automated meteorological text analysis is temporarily "
                    "unavailable due to high upstream API demand from Google Gemini infrastructure. "
                )
                # MATERIALIZE PUBLIC PORTFOLIO ASSET: Always runs, even if fallback text is engaged
            print("[AI Analyst] Materializing public portfolio ledger updates...")
            existing_history=""
            if os.path.exists("LATEST_METEROLOGY_REPORT.md"):
                with open("LATEST_METEROLOGY_REPORT.md", "r", encoding="utf-8") as h_file:
                    lines=h_file.readlines()
                    # Skip the first two lines
                    if len(lines) > 2:
                        existing_history = "".join(lines[2:])  # Keep the rest of the file after the first two lines
            # Re-write the file prepending the newest insights to the very top of the file, preserving historical content below
            
            with open("LATEST_METEROLOGY_REPORT.md", "w", encoding="utf-8") as md_file:
                    md_file.write(f"# Autonomous Global Weather Intelligence Bulletin\n\n")
                    
                    md_file.write(f"**Report Generation Window:** {db_now}  UTC\n\n")  

                    md_file.write("### START Gemini GenAI Safety Analysis\n") 
                    md_file.write(f"{ai_summary_text}\n\n")
                    md_file.write("\n\n### END Gemini GenAI Safety Analysis\n")

                    if existing_history:                        
                        md_file.write(existing_history)
            print("[AI Analyst] Public asset 'LATEST_METEOROLOGY_REPORT.md' successfully written.")           


if __name__ == "__main__":
    # Test gate for local verification
    analyst_agent = AIPipelineAnalyst()
    analyst_agent.generate_daily_report()

        