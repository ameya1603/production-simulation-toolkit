import random
import simpy
import pandas as pd

# Simulation Parameters
RANDOM_SEED = 42
NUM_STATIONS = 3
MEAN_PROCESSING_TIMES = [4, 6, 5]  # [Mfg 1, Mfg 2, Assembly Station]
STATION_NAMES = ["Mfg Machine 1", "Mfg Machine 2", "Assembly Station"]
INTERARRIVAL_TIME = 3              # Mean time between part arrivals
SIMULATION_TIME = 1000             # Total simulation duration

# Data collection trackers
part_data = []
station_busy_time = [0.0] * NUM_STATIONS
start_busy_time = [None] * NUM_STATIONS
parts_processed_count = [0] * NUM_STATIONS


def part_process(env, part_id, stations):
  arrival_time = env.now
  part_details = {
      "part_id": part_id,
      "arrival_system": arrival_time,
      "wait_time": [0.0] * NUM_STATIONS,
  }

  # Route part sequentially through the 3 stations
  for i in range(NUM_STATIONS):
    station = stations[i]
    start_wait = env.now

    # Request station resource (wait in queue if busy)
    station_request = station.request()
    yield station_request

    # Record waiting time
    wait_duration = env.now - start_wait
    part_details["wait_time"][i] = wait_duration

    # Process at the station
    processing_time = random.expovariate(1.0 / MEAN_PROCESSING_TIMES[i])
    start_busy_time[i] = env.now
    yield env.timeout(processing_time)
    start_busy_time[i] = None

    # Track station metrics
    station_busy_time[i] += processing_time
    parts_processed_count[i] += 1

    station.release(station_request)

  # Part completes the line
  cycle_time = env.now - arrival_time
  part_details["cycle_time"] = cycle_time
  part_data.append(part_details)


def part_source(env, stations):
  part_id = 0
  while True:
    time_to_next_arrival = random.expovariate(1.0 / INTERARRIVAL_TIME)
    yield env.timeout(time_to_next_arrival)
    part_id += 1
    env.process(part_process(env, part_id, stations))


# --- Run Simulation ---
print("--- Simulation Starting ---")
random.seed(RANDOM_SEED)
env = simpy.Environment()
stations = [simpy.Resource(env, capacity=1) for _ in range(NUM_STATIONS)]

env.process(part_source(env, stations))
env.run(until=SIMULATION_TIME)
print("--- Simulation Finished ---\n")

# Account for any stations still busy at the end of simulation time
for i in range(NUM_STATIONS):
  if start_busy_time[i] is not None:
    station_busy_time[i] += SIMULATION_TIME - start_busy_time[i]

# --- Compile Data into a Table ---
df_parts = pd.DataFrame(part_data)

summary_rows = []
for i in range(NUM_STATIONS):
  # Extract valid wait times for this specific station
  valid_waits = [w[i] for w in df_parts["wait_time"]] if not df_parts.empty else []
  avg_wait = sum(valid_waits) / len(valid_waits) if valid_waits else 0
  utilization = (station_busy_time[i] / SIMULATION_TIME) * 100
  throughput_rate = parts_processed_count[i] / SIMULATION_TIME

  summary_rows.append({
      "Station": STATION_NAMES[i],
      "Mean Proc Time (min)": MEAN_PROCESSING_TIMES[i],
      "Parts Processed": parts_processed_count[i],
      "Throughput (parts/min)": round(throughput_rate, 3),
      "Avg Wait Time (min)": round(avg_wait, 2),
      "Utilization (%)": f"{round(utilization, 2)}%",
  })

df_summary = pd.DataFrame(summary_rows)

# --- Print the Results Table ---
print("==================================================================")
print("             PRODUCTION LINE PERFORMANCE SUMMARY                  ")
print("==================================================================")
print(df_summary.to_string(index=False))
print("==================================================================")

if not df_parts.empty:
  overall_throughput = len(df_parts) / SIMULATION_TIME
  avg_cycle = df_parts["cycle_time"].mean()
  print(f"\nOverall Factory Metrics:")
  print(f" • Total Parts Finished : {len(df_parts)}")
  print(f" • Overall Throughput   : {overall_throughput:.3f} parts/minute")
  print(f" • Average Cycle Time   : {avg_cycle:.2f} minutes")