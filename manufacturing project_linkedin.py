import random
import salabim as sim

sim.yieldless(False)

# 1. Initialize the simulation environment and turn animation ON
env = sim.Environment(trace=False)
env.modelname("Production Line Simulation")
env.animate(True)  # Opens the visual animation window
env.speed(200)       # Controls animation speed
env.background_color("20%gray")

# Define processing speeds and station names
MEAN_PROCESSING_TIMES = [4, 6, 5]  # [Mfg 1, Mfg 2, Assembly]
STATION_NAMES = ["Mfg Machine 1", "Mfg Machine 2", "Assembly Station"]

# Create the 3 stations as Salabim Resources
stations = []
for i in range(3):
    station = sim.Resource(name=STATION_NAMES[i], capacity=1)
    stations.append(station)

# Add a title to the visual animation window
sim.AnimateText(
    text="Production Line: 2 Mfg Machines + 1 Assembly",
    x=50,
    y=550,
    fontsize=18,
    textcolor="white",
)

# Draw visual machine blocks and queue lines for each station on the canvas
for i in range(3):
    y_pos = 400 - (i * 100)
    
    # Station Name Label
    sim.AnimateText(text=STATION_NAMES[i], x=50, y=y_pos + 10, fontsize=14, textcolor="yellow")
    
    # Machine Box graphic
    sim.AnimateRectangle(spec=(220, y_pos - 5, 305, y_pos + 30), fillcolor="lightblue", linewidth=1)
    
    # Animate the waiting queue for this station
    stations[i].requesters().animate(x=350, y=y_pos + 10, direction="e", title="")


# 2. Define what happens to each Part (Component)
class Part(sim.Component):
    def animation_objects(self):
        # Defines how each part looks visually on screen (an orange box with its ID)
        return 30, 20, sim.AnimateRectangle(
            spec=(0, 0, 30, 20), 
            fillcolor="orange", 
            text=self.name(), 
            textcolor="black", 
            fontsize=10
        )

    def process(self):
        arrival_time = self.env.now()

        # Go through each station sequentially
        for i in range(3):
            # Request and wait in line for the station
            yield self.request(stations[i])

            # Simulate processing time at the machine
            processing_time = random.expovariate(1.0 / MEAN_PROCESSING_TIMES[i])
            yield self.hold(processing_time)

            # Release the station so the next part can use it
            self.release(stations[i])

        # Part exits the system
        cycle_time = self.env.now() - arrival_time
        print(f"Part {self.name()} finished in {cycle_time:.2f} minutes.")


# 3. Define the Part Generator (Source)
class Generator(sim.Component):
    def process(self):
        part_id = 0
        while True:
            # Time between part arrivals (Exponential distribution, mean = 3)
            interarrival_time = random.expovariate(1.0 / 3)
            yield self.hold(interarrival_time)

            part_id += 1
            Part(name=f"P{part_id}")


# Start the generator process
Generator()

# 4. Run the simulation (Fixed: use 'till' instead of 'until')
env.run(till=1000)