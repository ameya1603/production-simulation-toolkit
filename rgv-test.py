import math
import random
import matplotlib.pyplot as plt
import numpy as np

# --- Configuration & Parameters ---
TRACK_RADIUS = 1000.0  # mm (simplified circular track radius)
TRACK_CIRCUMFERENCE = 2 * math.pi * TRACK_RADIUS
NUM_VEHICLES = 2
SIMULATION_STEPS = 500
DT = 0.5  # Time step in seconds


class TrackSegment:

  def __init__(self, start_dist, end_dist, seg_type="straight"):
    self.dist0 = start_dist
    self.dist1 = end_dist
    self.type = seg_type  # 'straight' or 'curve'


class Task:

  def __init__(self, task_id, start_pos, end_pos):
    self.id = task_id
    self.start = start_pos
    self.end = end_pos
    self.state = "queued"  # queued, pending, transporting, finished
    self.now_time = 0


class RGV:

  def __init__(self, rgv_id, system, initial_dist):
    self.id = rgv_id
    self.system = system
    self.dist = initial_dist  # 1D natural coordinate along track
    self.speed = 0.0
    self.max_speed = 200.0  # mm/s
    self.max_speed_curve = 100.0  # mm/s
    self.carry_accel = 20.0  # mm/s^2
    self.empty_accel = 40.0  # mm/s^2
    self.state = "idle"  # idle, accel, decel, cruise
    self.task = None
    self.target = initial_dist
    self.carry = False

  def get_min_gap(self):
    return 150.0  # Minimum safe following distance in mm

  def get_brake_dis(self):
    accel = self.carry_accel if self.carry else self.empty_accel
    return (self.speed**2) / (2 * accel) if accel > 0 else 0

  def get_front_vehicle(self):
    # Find the closest vehicle ahead on the circular track
    other_vehicles = [v for v in self.system.vehicles if v != self]
    best_v = other_vehicles[0]
    min_dis = 1e18
    for v in other_vehicles:
      dis = self.system.A_to_B(self.dist, v.dist)
      if 0 < dis < min_dis:
        min_dis = dis
        best_v = v
    return best_v

  def assign_task(self, task, time):
    self.task = task
    self.target = self.system.stations[task.start]
    task.state = "pending"

  def accelerate(self, dt):
    accel = self.carry_accel if self.carry else self.empty_accel
    self.speed = min(self.speed + accel * dt, self.max_speed)
    self.dist = (self.dist + self.speed * dt) % self.system.max_dist

  def decelerate(self, stop_pos, dt):
    accel = self.carry_accel if self.carry else self.empty_accel
    self.speed = max(self.speed - accel * dt, 0.0)
    self.dist = (self.dist + self.speed * dt) % self.system.max_dist
    if np.isclose(self.speed, 0.0, atol=1e-2):
      self.speed = 0.0
      self.state = "idle"

  def cruise(self, dt):
    self.dist = (self.dist + self.speed * dt) % self.system.max_dist

  def give_way(self):
    self.state = "decel"
    self.speed = max(self.speed - 10, 0.0)

  def update(self, dt):
    if self.task:
      self.task.now_time += dt

    front_rgv = self.get_front_vehicle()
    distance_to_front = self.system.A_to_B(self.dist, front_rgv.dist)
    min_gap = self.get_min_gap()

    if self.state == "idle":
      if np.isclose(self.dist, self.target, atol=5.0):
        if self.task:
          if self.task.state == "pending":
            # Reached pickup point, now transporting
            self.task.state = "transporting"
            self.target = self.system.stations[self.task.end]
            self.carry = True
          elif self.task.state == "transporting":
            # Reached delivery point, task finished
            self.task.state = "finished"
            self.task = None
            self.carry = False
        return

      if distance_to_front <= min_gap + 5 and (
          front_rgv.state == "idle" or front_rgv.state == "decel"
      ):
        self.give_way()
        return

      self.state = "accel"
      self.accelerate(dt)
    else:
      # Check distance to vehicle ahead first!
      if distance_to_front <= min_gap + 10:
        # Match speed or brake to avoid collision
        self.state = "decel"
        self.speed = max(self.speed - 20 * dt, front_rgv.speed)
        self.dist = (self.dist + self.speed * dt) % self.system.max_dist
        return

      # Otherwise, check if destination reached
      dis_to_target = self.system.A_to_B(self.dist, self.target)
      if self.get_brake_dis() >= dis_to_target:
        self.state = "decel"
        self.decelerate(self.target, dt)
      elif np.isclose(self.speed, self.max_speed):
        self.state = "cruise"
        self.cruise(dt)
      else:
        self.state = "accel"
        self.accelerate(dt)


class RGVSystem:

  def __init__(self):
    self.max_dist = TRACK_CIRCUMFERENCE
    self.vehicles = []
    self.stations = {
        "Station_A": 0.0,
        "Station_B": 1500.0,
        "Station_C": 3000.0,
        "Station_D": 4500.0,
    }
    self.task_queue = []

  def A_to_B(self, posA, posB):
    # Calculate forward distance from posA to posB on circular track
    dis = posB - posA
    if dis < 0:
      dis += self.max_dist
    return dis

  def init_rgv(self, n_cars):
    for i in range(n_cars):
      initial_pos = i * (self.max_dist / n_cars)
      self.vehicles.append(RGV(i + 1, self, initial_pos))

  def assign_tasks(self):
    # Nearest Vehicle First Strategy
    idle_vehicles = [v for v in self.vehicles if v.task is None]
    queued_tasks = [t for t in self.task_queue if t.state == "queued"]

    for task in queued_tasks:
      if not idle_vehicles:
        break
      start_dist = self.stations[task.start]
      # Find closest idle RGV
      best_vehicle = min(
          idle_vehicles, key=lambda v: self.A_to_B(v.dist, start_dist)
      )
      best_vehicle.assign_task(task, 0)
      idle_vehicles.remove(best_vehicle)

  def update(self, dt):
      if self.task:
        self.task.now_time += dt

      front_rgv = self.get_front_vehicle()
      distance_to_front = self.system.A_to_B(self.dist, front_rgv.dist)
      min_gap = self.get_min_gap()

      # Default target is our task destination
      effective_target = self.target

      # If the front vehicle is stopped or we are getting close to it,
      # our effective target becomes the safe spot right behind the front vehicle.
      if distance_to_front <= self.get_brake_dis() + min_gap or front_rgv.state == "idle":
        front_backed_off_dist = front_rgv.dist - min_gap
        if front_backed_off_dist < 0:
          front_backed_off_dist += self.system.max_dist

        dist_to_my_target = self.system.A_to_B(self.dist, self.target)
        dist_to_front_target = self.system.A_to_B(self.dist, front_backed_off_dist)

        # Yield to the front vehicle if its blocking point is closer than our goal
        if dist_to_front_target < dist_to_my_target or front_rgv.state == "idle":
          effective_target = front_backed_off_dist

      # Distance to our current effective target
      dis_to_target = self.system.A_to_B(self.dist, effective_target)

      # Check if we have arrived and stopped at the target
      if np.isclose(self.dist, effective_target, atol=3.0) and np.isclose(self.speed, 0.0, atol=1e-2):
        self.speed = 0.0
        self.state = "idle"
        
        # If this effective target is our actual task destination (and not just a blocked yielding point)
        if np.isclose(effective_target, self.target, atol=3.0) and self.task:
          if self.task.state == "pending":
            # Reached pickup point
            self.task.state = "transporting"
            self.target = self.system.stations[self.task.end]
            self.carry = True
          elif self.task.state == "transporting":
            # Reached delivery point
            self.task.state = "finished"
            self.task = None
            self.carry = False
        return

      # Motion control logic (Accelerate, Decelerate, or Cruise)
      if self.get_brake_dis() >= dis_to_target:
        self.state = "decel"
        self.decelerate(effective_target, dt)
      elif self.speed < self.max_speed and front_rgv.state != "idle":
        self.state = "accel"
        self.accelerate(dt)
      else:
        self.state = "cruise"
        self.cruise(dt)


# --- Initialize Simulation & Run ---
print("Initializing RGV System Simulation...")
system = RGVSystem()
system.init_rgv(NUM_VEHICLES)

# Inject sample dynamic tasks
station_names = list(system.stations.keys())
for i in range(5):
  start = station_names[i % len(station_names)]
  end = station_names[(i + 2) % len(station_names)]
  system.task_queue.append(Task(f"T{i+1}", start, end))

# Setup Live Matplotlib Visualization
plt.ion()
fig, ax = plt.subplots(figsize=(6, 6))

for step in range(SIMULATION_STEPS):
  system.step(DT)

  # Render positions in Cartesian coordinates for visualization
  ax.clear()
  ax.set_xlim(-TRACK_RADIUS * 1.3, TRACK_RADIUS * 1.3)
  ax.set_ylim(-TRACK_RADIUS * 1.3, TRACK_RADIUS * 1.3)
  ax.set_title(
      f"RGV Circular Track Simulation (Time Step: {step * DT:.1f}s)", fontsize=12
  )

  # Draw Track Circle
  circle = plt.Circle((0, 0), TRACK_RADIUS, color="lightgray", fill=False, lw=4)
  ax.add_patch(circle)

  # Draw Stations
  for name, pos in system.stations.items():
    angle = (pos / system.max_dist) * 2 * math.pi
    sx = TRACK_RADIUS * math.cos(angle)
    sy = TRACK_RADIUS * math.sin(angle)
    ax.plot(sx, sy, "ro", markersize=8)
    ax.text(
        sx * 1.1,
        sy * 1.1,
        name,
        fontsize=9,
        ha="center",
        va="center",
        color="darkred",
    )

  # Draw Vehicles
  for v in system.vehicles:
    angle = (v.dist / system.max_dist) * 2 * math.pi
    vx = TRACK_RADIUS * math.cos(angle)
    vy = TRACK_RADIUS * math.sin(angle)
    color = "orange" if v.carry else "dodgerblue"
    ax.plot(vx, vy, marker="s", markersize=12, color=color)
    ax.text(
        vx,
        vy + 120,
        f"RGV {v.id}\n({v.state})",
        fontsize=8,
        ha="center",
        color="black",
    )

  plt.draw()
  plt.pause(0.05)

plt.ioff()
print("Simulation Completed Successfully!")
plt.show()