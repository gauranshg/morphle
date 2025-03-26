// Utility function: convert grid coordinate to pixel position.
function toPixel(pos) {
    return pos * 50;  // each cell is 50px
  }
  
  // Function to map backend color names to lighter shades.
  function mapColor(color) {
    if (color === "green") {
      return "#9be9a8";  // lighter GitHub-like green
    } else if (color === "red") {
      return "#ff9a8d";  // lighter red
    }
    return color; // fallback
  }
  
  // Update the UI based on backend status data.
  function updateUI(data) {
    console.log("Visited cells:", data.visited);
    const currentRegion = data.current_region;
    const target = data.target;
    const visited = data.visited;
    
    // Update current marker position.
    const currentMarker = document.getElementById('currentMarker');
    currentMarker.style.left = toPixel(currentRegion.x) + 'px';
    currentMarker.style.top = toPixel(currentRegion.y) + 'px';
    
    // Update target marker position.
    const targetMarker = document.getElementById('targetMarker');
    targetMarker.style.left = toPixel(target.x) + 'px';
    targetMarker.style.top = toPixel(target.y) + 'px';
    
    // Render visited cells:
    const container = document.getElementById('visitedContainer');
    // Clear existing visited cells.
    container.innerHTML = "";
    
    // Create cells based on the visited object.
    for (let key in visited) {
      if (visited.hasOwnProperty(key)) {
        let [x, y] = key.split(',').map(Number);
        let color = mapColor(visited[key]);
        let cellDiv = document.createElement('div');
        cellDiv.id = 'cell-' + key;
        cellDiv.className = 'cell';
        cellDiv.style.left = toPixel(x) + 'px';
        cellDiv.style.top = toPixel(y) + 'px';
        if (x === 0 && y === 0) {
          cellDiv.classList.add('start');
        }
        cellDiv.style.backgroundColor = color;
        container.appendChild(cellDiv);
      }
    }
  }
  
  // Poll the backend status with a variable interval.
  function pollStatus() {
    fetch('/status')
      .then(response => response.json())
      .then(data => {
        updateUI(data);
        // Determine next poll interval based on system state.
        let nextPollInterval = (data.state === "idle") ? 500 : 100;
        setTimeout(pollStatus, nextPollInterval);
      })
      .catch(err => {
        console.error("Error fetching status:", err);
        setTimeout(pollStatus, 2000);
      });
  }
  
  // Immediately fetch and update UI (used after key events and mouse clicks)
  function updateStatusNow() {
    fetch('/status')
      .then(response => response.json())
      .then(data => {
        updateUI(data);
      })
      .catch(err => {
        console.error("Error fetching immediate status:", err);
      });
  }
  
  // Start polling.
  pollStatus();
  
  // Listen for arrow key events.
  document.addEventListener('keydown', function(event) {
    let direction = null;
    if (event.key === "ArrowUp") direction = "up";
    else if (event.key === "ArrowDown") direction = "down";
    else if (event.key === "ArrowLeft") direction = "left";
    else if (event.key === "ArrowRight") direction = "right";
    
    if (direction) {
      fetch('/move', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ direction: direction })
      })
      .then(response => response.json())
      .then(data => {
        console.log("Move command result:", data);
        updateStatusNow();
      });
    }
  });
  
  // Listen for mouse clicks on the slide container to set target.
  document.getElementById('slide').addEventListener('click', function(event) {
    const slideRect = this.getBoundingClientRect();
    const clickX = event.clientX - slideRect.left;
    const clickY = event.clientY - slideRect.top;
    
    // Convert pixel coordinates to grid coordinates.
    const gridX = Math.floor(clickX / 50);
    const gridY = Math.floor(clickY / 50);
    
    // Send the target coordinates to the backend.
    fetch('/set_target', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ x: gridX, y: gridY })
    })
    .then(response => response.json())
    .then(data => {
      console.log("Set target result:", data);
      updateStatusNow();
    });
  });
  
  // Reset button event listener.
  document.getElementById('resetButton').addEventListener('click', function() {
    fetch('/reset', {
      method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
      console.log("Reset result:", data);
      updateStatusNow();
    });
  });
  