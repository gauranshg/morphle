import time
import threading
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

# Grid boundaries: columns 0..14 (15 columns) and rows 0..4 (5 rows)
MIN_X, MAX_X = 0, 14
MIN_Y, MAX_Y = 0, 4

# Global state variables:
# current_region: the cell where the camera currently is (grid coordinates)
current_region = {"x": 0, "y": 0}
# target: the desired cell computed from all move commands (initially same as current_region)
target = {"x": 0, "y": 0}
# visited: dictionary mapping "x,y" cell coordinates to its color.
# The starting cell (0,0) is marked as visited (green initially).
visited = {"0,0": "green"}
# state: one of "idle", "moving", or "capturing"
state = "idle"

# Lock to synchronize access to shared state.
lock = threading.Lock()

def worker():
    global current_region, target, state, visited
    while True:
        with lock:
            # Compute the difference between target and current position.
            dx = target["x"] - current_region["x"]
            dy = target["y"] - current_region["y"]
        
        # If already at target, nothing to do.
        if dx == 0 and dy == 0:
            time.sleep(0.1)
            continue

        # Decide next move. Here we choose vertical moves first.
        if dy != 0:
            next_move = {"axis": "y", "delta": 1 if dy > 0 else -1}
        elif dx != 0:
            next_move = {"axis": "x", "delta": 1 if dx > 0 else -1}
        else:
            next_move = None

        if next_move is not None:
            # Determine the new cell position after this step.
            new_region = current_region.copy()
            if next_move["axis"] == "x":
                new_region["x"] += next_move["delta"]
            else:
                new_region["y"] += next_move["delta"]

            # Begin move operation.
            state = "moving"
            print("Moving from", current_region, "to", new_region, "using move", next_move)
            time.sleep(3)  # Simulate move delay.

            with lock:
                # Update the current region.
                current_region = new_region.copy()
                coord = f"{current_region['x']},{current_region['y']}"
                # Mark visited cell as green if not already captured.
                if visited.get(coord) != "red":
                    visited[coord] = "green"
                print("Move complete. Current region:", current_region)

            # Wait 20ms to see if the target changes.
            time.sleep(0.02)
            with lock:
                # If the target hasn't moved, capture this cell.
                if current_region["x"] == target["x"] and current_region["y"] == target["y"]:
                    state = "capturing"
                    print("Capturing cell:", current_region)
                    time.sleep(2)  # Simulate capture delay.
                    visited[coord] = "red"
                    print("Capture complete on cell:", current_region)
                    state = "idle"
                else:
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
    
    This way, if commands cancel each other out, the net target reflects the minimal required displacement.
    """
    global target
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
        # Compute candidate target by adding the delta to the current target.
        candidate = {
            "x": target["x"] + delta["x"],
            "y": target["y"] + delta["y"]
        }
        # Enforce grid boundaries.
        if candidate["x"] < MIN_X or candidate["x"] > MAX_X or candidate["y"] < MIN_Y or candidate["y"] > MAX_Y:
            print(f"Move {direction} ignored. Candidate target {candidate} out of bounds.")
            return jsonify({"status": "ignored", "target_region": target})
        # Update the target.
        target = candidate.copy()
        print("Updated target:", target)
        # Compute effective pending net movement: target relative to current_region.
        net = {"x": target["x"] - current_region["x"], "y": target["y"] - current_region["y"]}
    return jsonify({"status": "command received", "target_region": target, "net_delta": net})

@app.route('/status')
def status():
    """
    Returns the current state of the system:
      - current_region: the current cell position (grid coordinates),
      - target: the current target cell,
      - state: current operation ("idle", "moving", or "capturing"),
      - visited: dictionary of visited cells and their colors.
    """
    with lock:
        return jsonify({
            "current_region": current_region,
            "target": target,
            "state": state,
            "visited": visited
        })

if __name__ == '__main__':
    # Start the background worker thread.
    worker_thread = threading.Thread(target=worker, daemon=True)
    worker_thread.start()
    app.run(debug=True)
