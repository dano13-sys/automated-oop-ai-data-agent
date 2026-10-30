import os
import requests
import duckdb
from datetime import datetime
import subprocess
from analyst import AIPipelineAnalyst

class WeatherDataIngestor:
    """
    An Object-Oriented data pipeline component engineered to securely authenticate,
    stream, and process raw meteorological data records into a local database.
    """
    def __init__(self):
        self.target_cities=["Toronto,CA", "Los Angeles,US", "London,GB", "Sydney,AU", "Tokyo,JP"]
        self.api_key = os.environ.get("OPENWEATHER_API_KEY")
        self.db_path ="weather_data.duckdb"
        #self.conn = duckdb.connect(self.db_path)

        #Ensure that api_key is not O, 0 or empty string
        if not self.api_key or self.api_key[0] in ["O", "0"]:
            raise ValueError("System Guard Alert: Invalid API key format! The passport number cannot begin with a numerical 0 or an alphabetical O.")


    def initialize_warehouse(self):
        # STEP 1: Boot up DuckDB and create/open the physical database file 
        #         by connecting directly to the relative file path stored in your constructor
        #conn = duckdb.connect(self.db_path)

        with duckdb.connect(self.db_path) as conn:
            sql_create_table = """
            CREATE TABLE IF NOT EXISTS raw_weather_logs (
                city VARCHAR,
                temperature DOUBLE,            
                pressure DOUBLE,
                humidity DOUBLE,
                extracted_at TIMESTAMP
            )
            """
            conn.execute(sql_create_table)

    def fetch_weather_data(self):
        """
        Connects to the public data utility network to stream and return 
        a parsed collection array of live meteorological logs.
        """

        # STEP 1: Create an empty list variable         
        weather_records = []

        # STEP 2: iterate through every individual city string sitting inside your encapsulated 'self.target_cities' list array.
        for city in self.target_cities:
            # STEP 3: build dynamic URL target string variable.
            #         The OpenWeatherMap endpoint layout expects this exact format:
            #         url = f"https://openweathermap.org{city}&appid={self.api_key}&units=metric"
            url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={self.api_key}&units=metric"

            # STEP 4: get the data from the url and store the response in a variable. Then, check if the response status code is 200 (OK). If it is, parse the JSON data from the response.
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                # STEP 5: Extract the relevant fields from the dictionary and append them to your list variable.
                print(f"Streaming data channel open for {city}... Raw payload received.")
                weather_records.append({
                    "city": city,
                    "temperature": data["main"]["temp"],
                    "pressure": data["main"]["pressure"],
                    "humidity": data["main"]["humidity"],
                    "extracted_at": datetime.fromtimestamp(data["dt"]).strftime('%Y-%m-%d %H:%M:%S')
                })
                
        return weather_records

    def load_records_to_warehouse(self, records):
        """
        Parses structured dictionary records from memory and executes 
        idempotent SQL insert queries to commit rows to DuckDB.
        """
        with duckdb.connect(self.db_path) as conn:
            for record in records:
                conn.execute("""
                    INSERT INTO raw_weather_logs (city, temperature, pressure, humidity, extracted_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (record["city"], record["temperature"], record["pressure"], record["humidity"], record["extracted_at"]))
                print(f"Data successfully committed to DuckDB table for {record['city']}.")

        
#execution gate
if __name__ == "__main__":
    print("===STARTING AUTONOMOUS WEATHER & AI PLATFORM===")
    my_test_object = WeatherDataIngestor()    
    my_test_object.initialize_warehouse()
    print(f"Success! Database warehouse file initialized smoothly.")

    #fire method to pull down data metric records
    extracted_records = my_test_object.fetch_weather_data()

    #pass those new records straight into DuckDB for storage
    my_test_object.load_records_to_warehouse(extracted_records)
    print(f"Success! {len(extracted_records)} records committed to DuckDB warehouse.")

    # Orchestration
    print("\nTriggering transformation engine compiler layer...")    
    #subprocess.run(["dbt", "run"], check=True)
    subprocess.run(["dbt", "run", "--profiles-dir", "."], check=True)
    print("\n dbt models built successfully.")  

    print("\n Handoff to AI Analytics Agent initiated...") 
    try:
        analyst_agent = AIPipelineAnalyst()
        analyst_agent.generate_daily_report()
    except Exception as e:
        print(f"[❌ AI ANALYST ERROR] Failed to execute: {e}")
    print("\n=== End-to-End Ingestion, Transformation, and AI Diagnostics Executed Successfully! ===")