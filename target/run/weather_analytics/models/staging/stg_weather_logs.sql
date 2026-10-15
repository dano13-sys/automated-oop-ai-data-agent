
    

    create  table
      "weather_data"."main_weather_data"."stg_weather_logs__dbt_tmp"
  
    
    as (
      with source_data as (
    select city,
    temperature,
    pressure,
    humidity,
    extracted_at
    from "weather_data"."main"."raw_weather_logs"
)

select city as city_node,
    temperature as current_temperature_celsius,
    pressure as barometric_pressure_hpa,
    humidity as humidity_percentage,
    extracted_at as recorded_at_timestamp
from source_data
    );
    
  