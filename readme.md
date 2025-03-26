# Real-Time Grid Navigation System

## Overview
This project simulates a grid-based navigation system where a moving marker finds the closest path to a target cell, updating in real time. The system features an interactive frontend with dark mode aesthetics and allows users to set the target position using both keyboard and mouse clicks.

## Features
- **Real-time movement visualization**: A bordered box moves dynamically to show the current position of the target.
- **Optimized status checking**: Updates are fetched only when required, reducing unnecessary requests.
- **Mouse & Keyboard Targeting**: Users can set target positions using either mouse clicks or keyboard inputs.
- **Path Optimization**: Instead of following a pre-defined path, the system calculates the closest path dynamically.
- **Speed Simulation**: Uses `time.sleep()` to simulate machine movement.
- **Modern UI**: Dark-themed interface with light green and red indicators for better visibility.
- **Reset Functionality**: Allows users to reset the system state at any time.
- **Docker Deployment**: Runs within a Docker container and can be deployed on Azure.

## Installation & Setup

### Prerequisites
- Docker installed on your system
- Azure account for deployment (if deploying to the cloud)

### Running Locally with Flask
1. Clone the repository:
   ```sh
   git clone https://github.com/gauranshg/morphle.git
   cd morphle
   ```
2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
3. Run the Flask application:
   ```sh
   python app.py
   ```
4. Access the system at `http://127.0.0.1:5000`

### Running with Docker
1. Build the Docker image:
   ```sh
   docker build -t grid-navigation .
   ```
2. Run the container:
   ```sh
   docker run -p 5000:5000 grid-navigation
   ```



## Author
Created by **Gauransh Gupta**
[LinkedIn Profile](https://www.linkedin.com/in/gauranshg)

