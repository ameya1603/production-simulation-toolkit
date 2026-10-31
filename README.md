# Smart Factory Logistics & RGV Simulation Suite

A comprehensive collection of discrete-event and kinematic simulation models for industrial manufacturing and automated intra-logistics, built using **Python**, **SimPy**, **Salabim**, and **Matplotlib**. 

This repository bridges classical production line flow optimization with advanced automated guided vehicle (RGV) motion control and task scheduling on circular track topologies.

---

## Projects Included in This Suite

### 1. Production Line Assembly Simulation (SimPy & Salabim)
* **Objective:** Model and optimize material flow through a sequential multi-stage production line (2 Manufacturing Machines + 1 Assembly Station).
* **Key Features:**
  * Stochastic modeling of processing times and part arrivals using exponential distributions.
  * Real-time 2D visual animation utilizing **Salabim** (featuring visual queues, custom component rendering, and live tracking).
  * Tabular performance summaries analyzing throughput rates, bottleneck identification, machine utilization, and waiting times.

### 2. Dynamic Rail Guided Vehicle (RGV) Circular Track Simulation
* **Objective:** Simulate automated material handling on a closed-loop circular track with multi-vehicle coordination.
* **Key Features:**
  * **Kinematic Motion Control:** Physics-based state machine handling acceleration, deceleration, cruising, and braking distance calculations ($v^2 - u^2 = 2ax$).
  * **Collision Avoidance & Traffic Rules:** Single-lane tracking that prevents vehicle overtaking, enforcing safe following gaps and smooth queueing behind stopped RGVs.
  * **Task Lifecycle State Machine:** Manages tasks through `queued` $\to$ `pending` $\to$ `transporting` $\to$ `finished` states.
  * **Real-Time Visual Rendering:** Live 2D Matplotlib animation displaying track geometry, station mapping, and vehicle load statuses.

---

## 🛠️ Tech Stack & Dependencies
* **Language:** Python 3.x
* **Simulation Libraries:** `SimPy`, `Salabim`
* **Math & Visualization:** `NumPy`, `Matplotlib`, `Pandas`

### Installation
Install the required dependencies via your terminal:
```bash
pip install simpy salabim numpy matplotlib pandas
