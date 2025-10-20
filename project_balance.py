import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# --- Project Configuration ---
PROJECT_NAME = "Project Balance"
OUTPUT_FILENAME = "project_balance_simulation.png"
#example date 
DAY_TO_SIMULATE = "2008-06-01" 

def load_home_demand_data(day_str):
    """Loads the real household energy demand for a specific day."""
    zip_url = "https://archive.ics.uci.edu/ml/machine-learning-databases/00235/household_power_consumption.zip"
    local_file = "household_power_consumption.txt"

    if not os.path.exists(local_file):
        raise FileNotFoundError(f"Please download and unzip the data from the UCI repository into the file: {local_file}")

    print("Loading and preparing home energy demand data...")
    df = pd.read_csv(
        local_file, sep=';', na_values=['?'],
        parse_dates={'datetime': ['Date', 'Time']},
        dayfirst=True, index_col='datetime'
    )
    df.ffill(inplace=True)
    
    df_day = df[df.index.strftime('%Y-%m-%d') == day_str].copy()
    df_day['demand_kw'] = df_day['Global_active_power'] 
    
    return df_day[['demand_kw']]

def generate_solar_profile(timeseries_index, peak_kw=4.0):
    """Generates a realistic solar power generation curve for a given day."""
    print("Generating simulated solar panel data...")
    hours = timeseries_index.hour + timeseries_index.minute / 60.0

    solar_curve = np.sin((hours - 7) * np.pi / 13).to_numpy()
    solar_curve[solar_curve < 0] = 0
    
    noise = np.random.normal(0, 0.05, len(solar_curve))
    solar_generation = (solar_curve + noise) * peak_kw
    solar_generation[solar_generation < 0] = 0
    
    return pd.DataFrame(solar_generation, index=timeseries_index, columns=['solar_kw'])

def generate_price_signal(timeseries_index):
    """Generates a dynamic time-of-use electricity price signal."""
    print("Generating simulated electricity price data...")
    prices = []
    base_price = 0.15  # $/kWh
    peak_price = 0.40  # $/kWh
    
    for time in timeseries_index:
        if 7 <= time.hour < 17: 
            prices.append(base_price)
        elif 17 <= time.hour < 21: 
            prices.append(peak_price)
        else: 
            prices.append(0.10)
            
    return pd.DataFrame(prices, index=timeseries_index, columns=['price_per_kwh'])

def generate_grid_signals(timeseries_index, event_chance=0.05):
    """Simulates random 'demand response' events from the grid operator."""
    print("Generating simulated grid stability signals...")
    per_minute_chance = event_chance / (24 * 60)
    grid_event = (np.random.random(len(timeseries_index)) < per_minute_chance).astype(int)
    return pd.DataFrame(grid_event, index=timeseries_index, columns=['grid_event'])

def create_simulation_plot(df):
    """Creates and saves a plot visualizing all the interacting signals."""
    print("Generating simulation environment plot...")
    fig, ax1 = plt.subplots(figsize=(15, 8))
   
    ax1.set_xlabel('Time of Day')
    ax1.set_ylabel('Power (kW)', color='tab:blue')
    ax1.plot(df.index, df['demand_kw'], color='tab:blue', label='Home Demand', alpha=0.8)
    ax1.plot(df.index, df['solar_kw'], color='tab:green', label='Solar Generation')
    ax1.tick_params(axis='y', labelcolor='tab:blue')
    ax1.grid(True, axis='y', linestyle='--')
    ax2 = ax1.twinx()
    ax2.set_ylabel('Price ($/kWh)', color='tab:red')
    ax2.plot(df.index, df['price_per_kwh'], color='tab:red', label='Grid Price', linestyle='--')
    ax2.tick_params(axis='y', labelcolor='tab:red')
    

    if df['grid_event'].sum() > 0:
    
        ax1.axvspan(df[df['grid_event']==1].index[0], df[df['grid_event']==1].index[0]+pd.Timedelta(minutes=1), color='purple', alpha=0.3, label='Grid Event')
        for time in df[df['grid_event'] == 1].index[1:]:
             ax1.axvspan(time, time + pd.Timedelta(minutes=1), color='purple', alpha=0.3)

    fig.legend(loc="upper right", bbox_to_anchor=(1,1), bbox_transform=ax1.transAxes)
    plt.title(f'{PROJECT_NAME}: Simulation Environment for {DAY_TO_SIMULATE}', fontsize=16)
    plt.savefig(OUTPUT_FILENAME)
    print(f"Plot saved as '{OUTPUT_FILENAME}'")

def main():
    """Main pipeline to build and visualize the simulation environment."""
    print(f"--- Initializing {PROJECT_NAME} Simulation Pipeline ---")
    
    try:
        df_demand = load_home_demand_data(DAY_TO_SIMULATE)
    except FileNotFoundError as e:
        print(f"\nError: {e}")
        print("Please ensure 'household_power_consumption.txt' is in the same directory.")
        return

    df_solar = generate_solar_profile(df_demand.index)
    df_price = generate_price_signal(df_demand.index)
    df_grid = generate_grid_signals(df_demand.index)
    
    print("Merging all data sources into a single simulation frame...")
    df_simulation = pd.concat([df_demand, df_solar, df_price, df_grid], axis=1)

    create_simulation_plot(df_simulation)
    
    print("\n--- Simulation Environment Ready ---")
    print("This script has created a simulated dataset and a plot visualizing it.")

if __name__ == '__main__':
    main()
