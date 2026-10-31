import simpy
import random
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

RANDOM_SEED = 42
NUM_STATIONS = 3
MEAN_PROCESSING_TIMES = [5, 7, 4]
INTERARRIVAL_TIME = 3
SIMULATION_TIME = 1000
TRACE = False  # Turned off trace for cleaner output

part_data = []
station_busy_time = [0.0] * NUM_STATIONS
start_busy_time = [None] * NUM_STATIONS


def part_process(env, part_id, stations):
    arrival_time_system = env.now
    part_details = {
        "part_id": part_id,
        "arrival_system": arrival_time_system,
        "station_entry": [None] * NUM_STATIONS,
        "service_start": [None] * NUM_STATIONS,
        "service_end": [None] * NUM_STATIONS,
        "wait_time": [None] * NUM_STATIONS,
    }
    
    processing_times = [random.expovariate(1.0 / MEAN_PROCESSING_TIMES[i]) for i in range(NUM_STATIONS)]
    
    for i in range(NUM_STATIONS):
        station = stations[i]
        part_details["station_entry"][i] = env.now
        
        station_request = station.request()
        yield station_request
        
        part_details["service_start"][i] = env.now
        part_details["wait_time"][i] = part_details["service_start"][i] - part_details["station_entry"][i]
        
        processing_time = processing_times[i]
        start_busy_time[i] = env.now
        yield env.timeout(processing_time)
        start_busy_time[i] = None
        
        part_details["service_end"][i] = env.now
        station_busy_time[i] += processing_time
        station.release(station_request)
        
    departure_time_system = env.now
    part_details["departure_system"] = departure_time_system
    part_details["cycle_time"] = departure_time_system - arrival_time_system
    part_data.append(part_details)


def part_source(env, stations):
    part_id_counter = 0
    while True:
        time_to_next_arrival = random.expovariate(1.0 / INTERARRIVAL_TIME)
        yield env.timeout(time_to_next_arrival)
        part_id_counter += 1
        env.process(part_process(env, part_id_counter, stations))


# --- Run Simulation ---
print("--- Assembly Line Simulation Starting ---")
random.seed(RANDOM_SEED)
env = simpy.Environment()
stations = [simpy.Resource(env, capacity=1) for _ in range(NUM_STATIONS)]
env.process(part_source(env, stations))
env.run(until=SIMULATION_TIME)
print("--- Simulation Finished ---\n")

# --- Results Analysis & Single Plot ---
df_parts = pd.DataFrame(part_data)
if not df_parts.empty:
    avg_cycle_time = df_parts["cycle_time"].mean()
    total_parts_produced = len(df_parts)
    throughput_rate = total_parts_produced / SIMULATION_TIME

    print(f"Total parts produced: {total_parts_produced}")
    print(f"Average cycle time per part: {avg_cycle_time:.2f} minutes")
    print(f"Throughput rate: {throughput_rate:.2f} parts per minute")

    # Plotting only 1 graph: Distribution of Part Cycle Times
    plt.figure(figsize=(8, 5))
    plt.hist(df_parts["cycle_time"].dropna(), bins=20, color="skyblue", edgecolor="black")
    plt.title("Distribution of Part Cycle Times", fontsize=14)
    plt.xlabel("Cycle Time (minutes)", fontsize=12)
    plt.ylabel("Number of Parts", fontsize=12)
    
    # Add a dashed red line for the average
    plt.axvline(avg_cycle_time, color="red", linestyle="dashed", linewidth=2, label=f"Average: {avg_cycle_time:.2f} min")
    
    plt.legend()
    plt.grid(axis='y', alpha=0.75)
    plt.tight_layout()
    plt.show()
else:
    print("No parts completed the process.")

print("\n--- End of Script ---")