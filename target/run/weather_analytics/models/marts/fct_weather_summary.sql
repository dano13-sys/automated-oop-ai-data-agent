
    

    create  table
      "weather_data"."main_weather_data"."fct_weather_summary__dbt_tmp"
  
    
    as (
      with staged_data as (
    select * from "weather_data"."main_weather_data"."stg_weather_logs"
),

time_windowed_metrics as (
    select
        city_node,        
        date_trunc('day', recorded_at_timestamp) as reading_date,
        current_temperature_celsius,
        barometric_pressure_hpa,
        humidity_percentage
    from staged_data
)

select
    city_node,
    reading_date,
    -- Calculate precise metrics isolated strictly within each day
    round(avg(current_temperature_celsius), 2) as avg_temperature_celsius,
    max(current_temperature_celsius) as max_temperature_celsius,
    min(current_temperature_celsius) as min_temperature_celsius,
    round(avg(humidity_percentage), 1) as avg_humidity_percentage,
    count(*) as total_hourly_snapshots_captured
from time_windowed_metrics
group by 
    city_node, 
    reading_date
order by 
    reading_date desc, 
    city_node
    );
    
  