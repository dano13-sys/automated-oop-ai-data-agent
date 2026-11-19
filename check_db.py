import duckdb

def inspect_weather_warehouse(db_path="weather_data.duckdb"):
    print(f"=== CONNECTING TO WAREHOUSE: {db_path} ===")
    conn = duckdb.connect(db_path)
    
    try:
        # 1. Audit and print all available tables inside your database instance
        print("\n📋 Discovering Schema Tables...")
        tables = conn.execute("SHOW ALL TABLES;").fetchall()
        if not tables:
            print("⚠️ The database file is currently completely empty.")
            return
            
        for t in tables:
            print(f"  └─ Table Found: {t[1]}.{t[2]}") # Prints database name + table name

        # 2. Extract and display row content from your raw tables         

        print("\n📊 Reviewing Latest Records in 'raw_weather_logs':")
        try:
            # We fetch up to 100 rows to keep your terminal output clean and scannable
            rows = conn.execute("""
                SELECT city, temperature, pressure, humidity, extracted_at
                FROM main.raw_weather_logs
                ORDER BY extracted_at DESC, city
                LIMIT 100;
            """).fetchall()

            if not rows:
                print("  ⚠️ 'raw_weather_logs' exists but contains 0 records.")
            else:
                # Column headers template matching your layout rules
                print(f"{'City':<15} | {'Date':<11} | {'Current Temp (°C)':<9} | {'Pressure (hpa)':<9} | {'Humidity (%)':<9}")
                print("-" * 85)
                for r in rows:
                    print(f"{r[0]:<15} | {str(r[4]):<11} | {r[1]:<9.2f} | {r[2]:<9.2f} | {r[3]:<9.2f}")
        except Exception as query_err:
            print(f"  ❌ Failed to query 'fct_weather_summary': {query_err}")

    finally:
        conn.close()
        print("\n=== CONNECTION CLOSED ===")

if __name__ == "__main__":
    inspect_weather_warehouse()