import time
import threading
import math
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

# Grid boundaries: columns 0..14 (15 columns) and rows 0..4 (5 rows)
MIN_X, MAX_X = 0, 14
MIN_Y, MAX_Y = 0, 4

# Global state variables:
current_region = {"x": 0, "y": 0}  # current cell position
target = {"x": 0, "y": 0}          # working target (updated incrementally)
final_destination = {"x": 0, "y": 0}  # final destination as intended by the latest move command
visited = {"0,0": "green"}         # visited cells: "green" means just visited, "red" means captured
state = "idle"

# Variables to manage journey delay based on block number.
blocks_traveled = 0

# Lock to synchronize access to shared state.
lock = threading.Lock()

def compute_delay(block_number):
    """
    Compute delay for the given block using:
      delay = 3*sqrt(block_number) - 3*sqrt(block_number-1)
    For block_number==1, this returns 3.
    """
    if block_number == 1:
        return 3.0
    return 3 * math.sqrt(block_number) - 3 * math.sqrt(block_number - 1)

def worker():
    global current_region, target, final_destination, state, visited, blocks_traveled
    while True:
        with lock:
            # Calculate the remaining distance toward the current target.
            dx = target["x"] - current_region["x"]
            dy = target["y"] - current_region["y"]

            # If no move is needed, reset the blocks counter.
            if dx == 0 and dy == 0:
                blocks_traveled = 0

        # No move needed? Short sleep then continue.
        if dx == 0 and dy == 0:
            time.sleep(0.1)
            continue

        # Decide the next move (vertical moves prioritized).
        if dy != 0:
            next_move = {"axis": "y", "delta": 1 if dy > 0 else -1}
        elif dx != 0:
            next_move = {"axis": "x", "delta": 1 if dx > 0 else -1}
        else:
            next_move = None

        if next_move is not None:
            # Determine the next cell.
            new_region = current_region.copy()
            if next_move["axis"] == "x":
                new_region["x"] += next_move["delta"]
            else:
                new_region["y"] += next_move["delta"]

            with lock:
                state = "moving"
                blocks_traveled += 1
                delay = compute_delay(blocks_traveled)
                print(f"Moving from {current_region} to {new_region} (block {blocks_traveled} delay {delay:.2f}s) using move {next_move}")

            time.sleep(delay)  # Delay based on block number

            with lock:
                current_region = new_region.copy()
                coord = f"{current_region['x']},{current_region['y']}"
                # Mark the cell as visited (green) if not already captured.
                if visited.get(coord) != "red":
                    visited[coord] = "green"
                print("Move complete. Current region:", current_region)

            # Brief chance for new move commands to arrive.
            time.sleep(0.02)

            with lock:
                # Only capture the cell if we've reached the final destination.
                if current_region["x"] == final_destination["x"] and current_region["y"] == final_destination["y"]:
                    state = "capturing"
                    print("Capturing cell:", current_region)
            # Only simulate capture delay if capturing is triggered.
            if state == "capturing":
                time.sleep(2)  # Simulate capture delay.
                with lock:
                    coord = f"{current_region['x']},{current_region['y']}"
                    visited[coord] = "red"
                    print("Capture complete on cell:", current_region)
                    state = "idle"
        else:
            time.sleep(0.1)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/move', methods=['POST'])
def move():
    """
    Receives a JSON payload with "direction" (up, down, left, right).
    Instead of queuing every move, update the global target.
    The new target is computed by adding one cell in the specified direction to the current target,
    then enforcing boundaries.
    
    Also update final_destination so that capture happens only once at the final cell.
    """
    global target, final_destination
    data = request.json
    direction = data.get('direction')

    # Map directions to move deltas.
    if direction == "up":
        delta = {"x": 0, "y": -1}
    elif direction == "down":
        delta = {"x": 0, "y": 1}
    elif direction == "left":
        delta = {"x": -1, "y": 0}
    elif direction == "right":
        delta = {"x": 1, "y": 0}
    else:
        return jsonify({"status": "invalid direction"})

    with lock:
        candidate = {
            "x": target["x"] + delta["x"],
            "y": target["y"] + delta["y"]
        }
        if candidate["x"] < MIN_X or candidate["x"] > MAX_X or candidate["y"] < MIN_Y or candidate["y"] > MAX_Y:
            print(f"Move {direction} ignored. Candidate target {candidate} out of bounds.")
            return jsonify({"status": "ignored", "target_region": target})
        # Update both target and final_destination.
        target = candidate.copy()
        final_destination = candidate.copy()
        print("Updated target and final destination:", target)
        net = {"x": target["x"] - current_region["x"], "y": target["y"] - current_region["y"]}
    return jsonify({"status": "command received", "target_region": target, "net_delta": net})

@app.route('/reset', methods=['POST'])
def reset():
    """
    Resets the system state to the starting conditions.
    """
    global current_region, target, final_destination, visited, blocks_traveled, state
    with lock:
        current_region = {"x": 0, "y": 0}
        target = {"x": 0, "y": 0}
        final_destination = {"x": 0, "y": 0}
        visited = {"0,0": "green"}
        blocks_traveled = 0
        state = "idle"
    print("System reset to initial state.")
    return jsonify({"status": "system reset"})

@app.route('/status')
def status():
    with lock:
        return jsonify({
            "current_region": current_region,
            "target": target,
            "final_destination": final_destination,
            "state": state,
            "visited": visited
        })

@app.route('/set_target', methods=['POST'])
def set_target():
    """
    Sets the target based on absolute grid coordinates sent from the front end.
    Expects JSON payload with keys 'x' and 'y'.
    """
    global target, final_destination
    data = request.json
    x = data.get('x')
    y = data.get('y')
    
    # Enforce grid boundaries.
    if x is None or y is None or x < MIN_X or x > MAX_X or y < MIN_Y or y > MAX_Y:
        return jsonify({"status": "ignored", "target_region": target})
    
    with lock:
        target = {"x": x, "y": y}
        final_destination = target.copy()
        print("Target updated via mouse click:", target)
    
    return jsonify({"status": "target updated", "target_region": target})


if __name__ == '__main__':
    worker_thread = threading.Thread(target=worker, daemon=True)
    worker_thread.start()
    app.run(debug=True)
    # app.run(host="0.0.0.0", port=80, debug=True)

