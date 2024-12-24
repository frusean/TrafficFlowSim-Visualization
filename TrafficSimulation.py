import numpy as np
import matplotlib.pyplot as plt
import simpy
import pygame
import tkinter as tk
from tkinter import messagebox
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import os

# Initialize Pygame
pygame.init()
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Traffic Simulation")


class Road:
    def __init__(self, name, capacity, coordinates=None):
        self.name = name
        self.capacity = capacity
        self.current_load = 0
        self.coordinates = coordinates
        self.history = []


class Vehicle:
    def __init__(self, id, weight, priority, speed=5):
        self.id = id
        self.weight = weight
        self.priority = priority
        self.x = np.random.randint(100, SCREEN_WIDTH - 100)
        self.y = 300 if id % 2 == 0 else 400  # Alternate between lanes
        self.color = (0, 128, 255) if priority > 2 else (255, 0, 0)
        self.speed = speed

    def move(self, congestion_level):
        """Move vehicle and adjust speed based on congestion level."""
        self.speed = max(1, int(5 * (1 - congestion_level)))  # Slow down in congestion
        self.x += self.speed
        if self.x > SCREEN_WIDTH:
            self.x = 0  # Loop back to the start of the road


class TrafficLight:
    def __init__(self, position):
        self.position = position
        self.state = 'green'
        self.timer = 0

    def update(self):
        """Update traffic light state based on timer."""
        self.timer += 1
        if self.state == 'green' and self.timer > 60:
            self.state = 'yellow'
            self.timer = 0
        elif self.state == 'yellow' and self.timer > 10:
            self.state = 'red'
            self.timer = 0
        elif self.state == 'red' and self.timer > 60:
            self.state = 'green'
            self.timer = 0

    def draw(self, screen):
        """Draw traffic light on screen."""
        color = (0, 255, 0) if self.state == 'green' else (255, 255, 0) if self.state == 'yellow' else (255, 0, 0)
        pygame.draw.circle(screen, color, self.position, 10)


def optimize_traffic_flow(roads, vehicles):
    assignments = {}
    for vehicle in vehicles:
        best_road = min(roads, key=lambda r: r.current_load / r.capacity)
        assignments[vehicle.id] = best_road.name
        best_road.current_load += vehicle.weight
    return assignments


def balance_traffic_flow(roads, vehicles):
    assignments = {}
    roads_sorted = sorted(roads, key=lambda road: road.current_load / road.capacity)
    for vehicle in vehicles:
        for road in roads_sorted:
            if road.current_load + vehicle.weight <= road.capacity:
                assignments[vehicle.id] = road.name
                road.current_load += vehicle.weight
                break
    return assignments


class TrafficSimulator:
    def __init__(self, env, roads, time_window=24, method="1", peak_hours=(8, 10), vehicle_rate=20):
        self.env = env
        self.roads = roads
        self.time_window = time_window
        self.vehicles = []
        self.method = method
        self.peak_hours = peak_hours
        self.vehicle_rate = vehicle_rate

    def add_vehicle(self, vehicle):
        self.vehicles.append(vehicle)
        self.env.process(self.vehicle_process(vehicle))

    def vehicle_process(self, vehicle):
        if self.method == "1":
            assignments = optimize_traffic_flow(self.roads, [vehicle])
        else:
            assignments = balance_traffic_flow(self.roads, [vehicle])

        road_name = assignments[vehicle.id]
        assigned_road = next(road for road in self.roads if road.name == road_name)
        assigned_road.current_load += vehicle.weight
        yield self.env.timeout(1)
        assigned_road.current_load = max(0, assigned_road.current_load - vehicle.weight)
        assigned_road.history.append(assigned_road.current_load / assigned_road.capacity)

    def generate_random_traffic(self):
        for hour in range(self.time_window):
            is_peak = self.peak_hours[0] <= hour <= self.peak_hours[1]
            rate = self.vehicle_rate if is_peak else int(self.vehicle_rate / 2)
            num_vehicles = np.random.poisson(rate)
            for _ in range(num_vehicles):
                vehicle = Vehicle(id=len(self.vehicles), weight=np.random.choice([1, 2, 3]),
                                  priority=np.random.choice([1, 2, 3, 4, 5]))
                self.add_vehicle(vehicle)
            yield self.env.timeout(1)

    def run_matplotlib_visualization(self):
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))

        # Congestion Levels Over Time with Annotations
        for road in self.roads:
            ax1.plot(road.history, label=f'{road.name} Congestion Level')
            for i, value in enumerate(road.history):
                if i % 20 == 0:  # Annotate every 20th point for clarity
                    ax1.annotate(f"{value * 100:.2f}%", (i, value), textcoords="offset points", xytext=(0, 5),
                                 ha='center')
        ax1.set_title("Congestion Levels Over Time")
        ax1.set_xlabel("Time (units)")
        ax1.set_ylabel("Congestion Level (%)")
        ax1.legend()
        ax1.grid(True)

        # Vehicle Counts Over Time with Annotations
        for road in self.roads:
            vehicle_counts = [load * road.capacity for load in road.history]
            ax2.plot(vehicle_counts, label=f'{road.name} Vehicle Count')
            for i, value in enumerate(vehicle_counts):
                if i % 20 == 0:  # Annotate every 20th point
                    ax2.annotate(f"{int(value)}", (i, value), textcoords="offset points", xytext=(0, 5), ha='center')
        ax2.set_title("Vehicle Counts Over Time")
        ax2.set_xlabel("Time (units)")
        ax2.set_ylabel("Number of Vehicles")
        ax2.legend()
        ax2.grid(True)

        # System Throughput with Annotations
        total_throughput = [sum(road.current_load for road in self.roads) for _ in range(len(self.roads[0].history))]
        ax3.plot(total_throughput, color="blue")
        for i, value in enumerate(total_throughput):
            if i % 20 == 0:  # Annotate every 20th point
                ax3.annotate(f"{int(value)}", (i, value), textcoords="offset points", xytext=(0, 5), ha='center')
        ax3.set_title("System Throughput")
        ax3.set_xlabel("Time (units)")
        ax3.set_ylabel("Total Vehicles in System")
        ax3.grid(True)

        # Average Congestion by Road with Detailed Labels
        avg_congestion = {road.name: np.mean(road.history) * 100 for road in self.roads}
        ax4.bar(avg_congestion.keys(), avg_congestion.values())
        for i, (name, value) in enumerate(avg_congestion.items()):
            ax4.text(i, value, f"{value:.2f}%", ha='center', va='bottom')  # Show values on top of bars
        ax4.set_title("Average Congestion by Road")
        ax4.set_ylabel("Average Congestion Level (%)")

        plt.tight_layout()
        plt.show()
        fig.savefig("traffic_simulation_summary.png")
        plt.close(fig)

    def generate_pdf_report(self):
        """Generate a detailed PDF report with specific performance metrics for each road, including units of measurement and the algorithm used."""
        pdf_file = "traffic_simulation_report.pdf"
        c = canvas.Canvas(pdf_file, pagesize=A4)
        width, height = A4

        # Title and Heading
        c.setFont("Helvetica-Bold", 16)
        c.drawString(100, height - 50, "Traffic Simulation Detailed Report")

        # Display Algorithm Used
        algorithm_name = "Knapsack Approach" if self.method == "1" else "Balanced Traffic Approach"
        c.setFont("Helvetica", 12)
        y_position = height - 80
        c.drawString(100, y_position, f"Algorithm Used: {algorithm_name}")

        # Summary and Metrics Section
        y_position -= 30
        c.drawString(100, y_position, "Highway Performance Summary:")
        y_position -= 20

        # Detailed metrics for each road
        for road in self.roads:
            avg_congestion = np.mean(road.history) * 100 if road.history else 0
            peak_congestion = max(road.history) * 100 if road.history else 0
            min_congestion = min(road.history) * 100 if road.history else 0
            high_congestion_periods = sum(1 for x in road.history if x > 0.7)  # High congestion is over 70%
            total_vehicles = sum([load * road.capacity for load in road.history])

            c.drawString(100, y_position, f"{road.name} Highway Performance:")
            y_position -= 15
            c.drawString(120, y_position, f"- Average Congestion Level: {avg_congestion:.2f}%")
            y_position -= 15
            c.drawString(120, y_position, f"- Peak Congestion Level: {peak_congestion:.2f}%")
            y_position -= 15
            c.drawString(120, y_position, f"- Minimum Congestion Level: {min_congestion:.2f}%")
            y_position -= 15
            c.drawString(120, y_position, f"- Total Vehicles Processed: {int(total_vehicles)} vehicles")
            y_position -= 15
            c.drawString(120, y_position, f"- High Congestion Periods (>70%): {high_congestion_periods} hours")
            y_position -= 25

        # Insert the Matplotlib visualization image
        y_position -= 50
        if os.path.exists("traffic_simulation_summary.png"):
            c.drawImage("traffic_simulation_summary.png", 50, y_position - 300, width=500, height=250)

        # Save and close PDF
        c.save()
        messagebox.showinfo("Report Saved", f"Simulation report saved as {pdf_file}")


def draw_road_layout():
    pygame.draw.line(screen, (255, 255, 255), (100, 300), (700, 300), 5)
    pygame.draw.line(screen, (255, 255, 255), (100, 400), (700, 400), 5)
    font = pygame.font.Font(None, 36)
    screen.blit(font.render("Mandela", True, (255, 255, 255)), (10, 280))
    screen.blit(font.render("Portmore", True, (255, 255, 255)), (10, 380))


def draw_vehicles_on_roads(vehicles, roads, congestion_level):
    for vehicle in vehicles:
        vehicle.move(congestion_level)
        pygame.draw.circle(screen, vehicle.color, (vehicle.x, vehicle.y), 5)


def run_simulation_with_visualization(roads, time_window=24, method="1", peak_hours=(8, 10), vehicle_rate=20):
    env = simpy.Environment()
    simulator = TrafficSimulator(env, roads, time_window, method, peak_hours, vehicle_rate)
    env.process(simulator.generate_random_traffic())

    traffic_light = TrafficLight((SCREEN_WIDTH // 2, 350))  # Place traffic light at midpoint of road

    clock = pygame.time.Clock()
    running = True
    while running and env.peek() <= time_window:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        screen.fill((0, 0, 0))
        draw_road_layout()
        traffic_light.update()
        traffic_light.draw(screen)

        env.step()
        congestion_level = min(1, sum(road.current_load / road.capacity for road in roads) / len(roads))
        draw_vehicles_on_roads(simulator.vehicles, roads, congestion_level)

        font = pygame.font.Font(None, 36)
        for i, road in enumerate(roads):
            screen.blit(font.render(f"{road.name} Load: {road.current_load}/{road.capacity}", True, (255, 255, 255)),
                        (10, 10 + i * 30))

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()
    simulator.run_matplotlib_visualization()
    simulator.generate_pdf_report()


def start_simulation(selected_method, time_window, peak_hours, vehicle_rate, road_capacities):
    roads = [
        Road("Mandela", capacity=road_capacities[0], coordinates=(18.0116, -76.8102)),
        Road("Portmore", capacity=road_capacities[1], coordinates=(17.9509, -76.8822))
    ]
    run_simulation_with_visualization(roads, time_window, selected_method, peak_hours, vehicle_rate)


def create_gui():
    root = tk.Tk()
    root.title("Traffic Simulation")

    title_label = tk.Label(root, text="Traffic Congestion Simulation", font=("Arial", 16, "bold"))
    title_label.pack(pady=10)
    heading_label = tk.Label(root, text="Select Traffic Management Algorithm and Parameters", font=("Arial", 12))
    heading_label.pack(pady=5)

    selected_method = tk.StringVar(value="1")
    tk.Radiobutton(root, text="Knapsack Approach", variable=selected_method, value="1").pack(anchor="w", padx=20)
    tk.Radiobutton(root, text="Balanced Traffic Approach", variable=selected_method, value="2").pack(anchor="w",
                                                                                                     padx=20)

    tk.Label(root, text="Time Window (hours):").pack(anchor="w", padx=20)
    time_window_entry = tk.Entry(root)
    time_window_entry.insert(0, "24")
    time_window_entry.pack(anchor="w", padx=20)

    peak_period = tk.StringVar(value="morning")
    tk.Label(root, text="Select Peak Hours Period:").pack(anchor="w", padx=20)
    tk.Radiobutton(root, text="Morning Peak (6 - 8 AM)", variable=peak_period, value="morning").pack(anchor="w",
                                                                                                     padx=40)
    tk.Radiobutton(root, text="Midday Peak (11:30 AM - 1:30 PM)", variable=peak_period, value="midday").pack(anchor="w",
                                                                                                             padx=40)
    tk.Radiobutton(root, text="Evening Peak (4 - 7 PM)", variable=peak_period, value="evening").pack(anchor="w",
                                                                                                     padx=40)

    tk.Label(root, text="Average Vehicle Entry Rate (vehicles/hour):").pack(anchor="w", padx=20)
    vehicle_rate_entry = tk.Entry(root)
    vehicle_rate_entry.insert(0, "20")
    vehicle_rate_entry.pack(anchor="w", padx=20)

    tk.Label(root, text="Road Capacities:").pack(anchor="w", padx=20)
    road1_capacity_entry = tk.Entry(root)
    road1_capacity_entry.insert(0, "1000")
    road1_capacity_entry.pack(anchor="w", padx=20)

    road2_capacity_entry = tk.Entry(root)
    road2_capacity_entry.insert(0, "800")
    road2_capacity_entry.pack(anchor="w", padx=20)

    def on_start():
        method = selected_method.get()
        time_window = int(time_window_entry.get())
        peak_hours = (6, 8) if peak_period.get() == "morning" else (11.5, 13.5) if peak_period.get() == "midday" else (
        16, 19)
        vehicle_rate = int(vehicle_rate_entry.get())
        road_capacities = [int(road1_capacity_entry.get()), int(road2_capacity_entry.get())]

        root.destroy()
        start_simulation(method, time_window, peak_hours, vehicle_rate, road_capacities)

    start_button = tk.Button(root, text="Start Simulation", command=on_start)
    start_button.pack(pady=20)

    root.mainloop()


create_gui()