# TrafficFlowSim

## Overview
TrafficFlowSim is a Python-based traffic congestion simulation tool that models vehicle movement across roads, simulating real-world congestion and traffic light behavior. This project uses SimPy for event-driven simulation, Pygame for visualization, and Matplotlib for data analysis and reporting.

## Features
- **Real-Time Traffic Visualization**  
  Vehicles move dynamically, and congestion levels influence vehicle speed.
- **Traffic Management Algorithms**  
  - Knapsack Approach (Optimized traffic flow)
  - Balanced Traffic Distribution
- **Graphical User Interface (GUI)**  
  Configure simulation parameters such as peak hours, vehicle rates, and road capacities using Tkinter.
- **Reporting and Visualization**  
  Generates PDF reports with graphs detailing congestion levels, throughput, and road performance.

## Technologies Used
- Python
- SimPy (Event-driven simulation)
- Pygame (Visualization)
- Matplotlib (Graphs and charts)
- Tkinter (GUI)
- ReportLab (PDF generation)
- NumPy (Mathematical operations)

## How It Works
1. Users configure traffic simulation settings via the GUI.
2. The simulation generates random vehicles and distributes them across roads.
3. Traffic lights change states, influencing vehicle movement.
4. Congestion levels are monitored and visualized in real-time.
5. Post-simulation, Matplotlib graphs and PDF reports summarize performance metrics.

## Installation
1. Clone the repository:
   ```bash
   git clone <repo-url>
   ```
2. Navigate to the project directory:
   ```bash
   cd TrafficFlowSim
   ```
3. Install dependencies:
   ```bash
   pip install pygame simpy numpy matplotlib reportlab
   ```

## Usage
1. Run the simulation:
   ```bash
   python traffic_simulator.py
   ```
2. Adjust parameters through the GUI and start the simulation.
3. Visualize real-time traffic and review the PDF report after the simulation.

## File Structure
```
TrafficFlowSim/
|-- traffic_simulator.py  # Main simulation script
|-- README.md             # Project documentation
|-- requirements.txt      # List of dependencies
|-- traffic_simulation_summary.png  # Visualization output
|-- traffic_simulation_report.pdf   # PDF report (Generated post-simulation)
```

## Example
- **Scenario:** Simulate traffic on Mandela and Portmore roads.
- **Parameters:**
  - Time Window: 24 hours
  - Peak Hours: 6 AM - 8 AM
  - Vehicle Entry Rate: 20 vehicles/hour

## Contributing
Feel free to submit issues or fork the project to add more features. Contributions are welcome!

## License
MIT License
