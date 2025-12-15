/**
 * Smart Poultry Heater Control System - JavaScript
 * Handles real-time data updates from MySQL database via API
 */

// ============================================
// Configuration
// ============================================

const CONFIG = {
  apiBaseUrl: "api.php", // API endpoint
  updateInterval: 5000, // 5 seconds
  chartUpdateInterval: 10000, // 10 seconds
  deviceCount: 3, // Updated to match actual device count
  maxChartPoints: 20,
};

// ============================================
// State Management
// ============================================

const state = {
  devices: [],
  sensorData: {
    temperature: [],
    humidity: [],
    light: [],
  },
  heaterStates: [],
  controlMode: "auto",
  isConnected: false,
  stats: null,
};

// ============================================
// API Functions
// ============================================

async function fetchAPI(action, params = {}) {
  try {
    const queryString = new URLSearchParams({ action, ...params }).toString();
    const response = await fetch(`${CONFIG.apiBaseUrl}?${queryString}`);

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();

    if (data.status === "error") {
      throw new Error(data.message);
    }

    return data.data;
  } catch (error) {
    console.error(`API Error (${action}):`, error);
    throw error;
  }
}

async function postAPI(action, data) {
  try {
    const response = await fetch(`${CONFIG.apiBaseUrl}?action=${action}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const result = await response.json();

    if (result.status === "error") {
      throw new Error(result.message);
    }

    return result.data;
  } catch (error) {
    console.error(`API Error (${action}):`, error);
    throw error;
  }
}

// ============================================
// Initialize Application
// ============================================

document.addEventListener("DOMContentLoaded", () => {
  console.log("🚀 Initializing Smart Poultry Heater Control System...");

  initializeTheme();
  initializeCharts();
  setupEventListeners();
  startDataUpdates();

  console.log("✅ System initialized successfully!");
});

// ============================================
// Theme Management
// ============================================

function initializeTheme() {
  const savedTheme = localStorage.getItem("theme") || "dark";
  document.documentElement.setAttribute("data-theme", savedTheme);
  console.log(`🎨 Theme initialized: ${savedTheme}`);
}

function toggleTheme() {
  const currentTheme = document.documentElement.getAttribute("data-theme");
  const newTheme = currentTheme === "dark" ? "light" : "dark";

  document.documentElement.setAttribute("data-theme", newTheme);
  localStorage.setItem("theme", newTheme);

  console.log(`🎨 Theme switched to: ${newTheme}`);
}

// ============================================
// Device Management
// ============================================

async function loadDevices() {
  try {
    const data = await fetchAPI("devices");
    state.devices = data.devices;
    renderDevices();
    updateDashboardMetrics();
    updateSystemStatus(data.count);
  } catch (error) {
    console.error("Failed to load devices:", error);
    showNotification("Failed to load devices", "error");
  }
}

function renderDevices() {
  const container = document.getElementById("devices-container");
  if (!container) return;

  container.innerHTML = "";

  if (state.devices.length === 0) {
    container.innerHTML = `
      <div style="grid-column: 1 / -1; text-align: center; padding: 2rem; color: var(--text-secondary);">
        <p>No devices found. Make sure the MQTT bridge is running and devices are publishing data.</p>
      </div>
    `;
    return;
  }

  state.devices.forEach((device) => {
    const deviceCard = createDeviceCard(device);
    container.appendChild(deviceCard);
  });
}

function createDeviceCard(device) {
  const card = document.createElement("div");
  card.className = "device-card";
  card.setAttribute("data-device-id", device.id);

  const reading = device.latest_reading || {};
  const hasData = reading.temperature !== null;

  card.innerHTML = `
    <div class="device-header">
      <h3 class="device-name">${device.name}</h3>
      <span class="device-status ${device.status}">${device.status}</span>
    </div>
    
    ${
      hasData
        ? `
      <div class="device-readings">
        <div class="device-reading">
          <div class="reading-label">Temperature</div>
          <div class="reading-value">
            ${reading.temperature.toFixed(1)}
            <span class="reading-unit">°C</span>
          </div>
        </div>
        <div class="device-reading">
          <div class="reading-label">Humidity</div>
          <div class="reading-value">
            ${reading.humidity.toFixed(1)}
            <span class="reading-unit">%</span>
          </div>
        </div>
        <div class="device-reading">
          <div class="reading-label">Light</div>
          <div class="reading-value">
            ${reading.ldr.toFixed(1)}
            <span class="reading-unit">%</span>
          </div>
        </div>
      </div>
      
      <div class="device-controls">
        <button class="btn ${reading.heater ? "btn-danger" : "btn-success"}" 
                onclick="toggleHeater(${device.id})">
          <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                  d="M17.657 18.657A8 8 0 016.343 7.343S7 9 9 10c0-2 .5-5 2.986-7C14 5 16.09 5.777 17.656 7.343A7.975 7.975 0 0120 13a7.975 7.975 0 01-2.343 5.657z" />
          </svg>
          Heater ${reading.heater ? "ON" : "OFF"}
        </button>
        <button class="btn btn-secondary" onclick="viewDeviceDetails(${
          device.id
        })">
          <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                  d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          Details
        </button>
      </div>
    `
        : `
      <div style="padding: 2rem; text-align: center; color: var(--text-secondary);">
        <p>No data available yet</p>
        <p style="font-size: 0.875rem; margin-top: 0.5rem;">Waiting for sensor readings...</p>
      </div>
    `
    }
  `;

  return card;
}

async function toggleHeater(deviceId) {
  const device = state.devices.find((d) => d.id === deviceId);
  if (!device) return;

  if (state.controlMode === "auto") {
    alert(
      "⚠️ System is in AUTO mode. Switch to MANUAL mode to control heaters manually."
    );
    return;
  }

  try {
    const newState = device.latest_reading.heater ? 0 : 1;

    await postAPI("control", {
      device_id: deviceId,
      command: "heater",
      value: newState,
      source: "web_interface",
    });

    console.log(
      `🔥 Device ${deviceId} heater command sent: ${newState ? "ON" : "OFF"}`
    );
    showNotification(
      `Heater ${newState ? "ON" : "OFF"} command sent to Device ${deviceId}`,
      "success"
    );

    // Refresh devices after a short delay
    setTimeout(loadDevices, 1000);
  } catch (error) {
    console.error("Failed to toggle heater:", error);
    showNotification("Failed to send heater command", "error");
  }
}

function viewDeviceDetails(deviceId) {
  const device = state.devices.find((d) => d.id === deviceId);
  if (!device) return;

  const reading = device.latest_reading || {};

  alert(
    `📊 ${device.name} Details\n\n` +
      `Status: ${device.status}\n` +
      `Type: ${device.type}\n` +
      `Last Seen: ${
        device.last_seen ? new Date(device.last_seen).toLocaleString() : "Never"
      }\n\n` +
      `Latest Reading:\n` +
      `Temperature: ${
        reading.temperature ? reading.temperature.toFixed(1) + "°C" : "N/A"
      }\n` +
      `Humidity: ${
        reading.humidity ? reading.humidity.toFixed(1) + "%" : "N/A"
      }\n` +
      `Light: ${reading.ldr ? reading.ldr.toFixed(1) + "%" : "N/A"}\n` +
      `Heater: ${
        reading.heater !== null ? (reading.heater ? "ON" : "OFF") : "N/A"
      }\n` +
      `Confidence: ${
        reading.confidence ? (reading.confidence * 100).toFixed(1) + "%" : "N/A"
      }\n` +
      `Timestamp: ${
        reading.timestamp ? new Date(reading.timestamp).toLocaleString() : "N/A"
      }`
  );
}

// ============================================
// Dashboard Metrics
// ============================================

async function loadStats() {
  try {
    const stats = await fetchAPI("stats");
    state.stats = stats;
    updateDashboardMetrics();
  } catch (error) {
    console.error("Failed to load stats:", error);
  }
}

function updateDashboardMetrics() {
  if (!state.stats) return;

  // Update temperature
  updateElement("avg-temp", state.stats.temperature.average || "--");
  updateElement(
    "temp-range",
    `${state.stats.temperature.min || "--"}°C - ${
      state.stats.temperature.max || "--"
    }°C`
  );

  // Update humidity
  updateElement("avg-humidity", state.stats.humidity.average || "--");
  updateElement(
    "humidity-range",
    `${state.stats.humidity.min || "--"}% - ${
      state.stats.humidity.max || "--"
    }%`
  );

  // Update light
  updateElement("avg-light", state.stats.light.average || "--");
  updateElement(
    "light-range",
    `${state.stats.light.min || "--"}% - ${state.stats.light.max || "--"}%`
  );

  // Count heaters on from devices
  const heatersOn = state.devices.filter(
    (d) => d.latest_reading && d.latest_reading.heater === 1
  ).length;

  updateElement("heaters-on", heatersOn);
  updateElement("total-devices", state.devices.length);
  updateElement(
    "heater-percentage",
    state.devices.length > 0
      ? `${((heatersOn / state.devices.length) * 100).toFixed(0)}%`
      : "0%"
  );

  // Update heater indicators
  const indicators = document.querySelectorAll(".heater-indicator");
  indicators.forEach((indicator, index) => {
    const device = state.devices[index];
    if (device && device.latest_reading) {
      indicator.className = `heater-indicator ${
        device.latest_reading.heater ? "on" : "off"
      }`;
    }
  });

  // Update confidence gauge
  const avgConfidence = state.stats.avg_confidence || 0;
  updateElement("confidence-value", Math.round(avgConfidence));
  updateConfidenceGauge(avgConfidence);

  // Update model accuracy
  updateElement("model-accuracy", `${avgConfidence.toFixed(1)}%`);
}

function updateSystemStatus(deviceCount) {
  updateElement("total-devices", deviceCount || CONFIG.deviceCount);
}

function updateElement(id, value) {
  const element = document.getElementById(id);
  if (element) {
    element.textContent = value;
  }
}

function updateConfidenceGauge(confidence) {
  const arc = document.getElementById("confidence-arc");
  if (!arc) return;

  // Calculate stroke-dashoffset (251.2 is the full arc length)
  const offset = 251.2 - 251.2 * (confidence / 100);
  arc.style.strokeDashoffset = offset;
}

// ============================================
// Charts
// ============================================

let tempChart, humidityChart, lightChart, historicalChart;

function initializeCharts() {
  // Temperature Chart
  const tempCtx = document.getElementById("temp-chart");
  if (tempCtx) {
    tempChart = new Chart(tempCtx, {
      type: "line",
      data: {
        labels: [],
        datasets: [
          {
            label: "Temperature",
            data: [],
            borderColor: "#ff6b6b",
            backgroundColor: "rgba(255, 107, 107, 0.1)",
            borderWidth: 2,
            tension: 0.4,
            fill: true,
          },
        ],
      },
      options: getChartOptions("°C"),
    });
  }

  // Humidity Chart
  const humidityCtx = document.getElementById("humidity-chart");
  if (humidityCtx) {
    humidityChart = new Chart(humidityCtx, {
      type: "line",
      data: {
        labels: [],
        datasets: [
          {
            label: "Humidity",
            data: [],
            borderColor: "#4facfe",
            backgroundColor: "rgba(79, 172, 254, 0.1)",
            borderWidth: 2,
            tension: 0.4,
            fill: true,
          },
        ],
      },
      options: getChartOptions("%"),
    });
  }

  // Light Chart
  const lightCtx = document.getElementById("light-chart");
  if (lightCtx) {
    lightChart = new Chart(lightCtx, {
      type: "line",
      data: {
        labels: [],
        datasets: [
          {
            label: "Light",
            data: [],
            borderColor: "#ffd93d",
            backgroundColor: "rgba(255, 217, 61, 0.1)",
            borderWidth: 2,
            tension: 0.4,
            fill: true,
          },
        ],
      },
      options: getChartOptions("%"),
    });
  }

  // Historical Chart
  const historicalCtx = document.getElementById("historical-chart");
  if (historicalCtx) {
    historicalChart = new Chart(historicalCtx, {
      type: "line",
      data: {
        labels: [],
        datasets: [
          {
            label: "Temperature (°C)",
            data: [],
            borderColor: "#ff6b6b",
            backgroundColor: "rgba(255, 107, 107, 0.1)",
            borderWidth: 2,
            tension: 0.4,
            yAxisID: "y",
          },
          {
            label: "Humidity (%)",
            data: [],
            borderColor: "#4facfe",
            backgroundColor: "rgba(79, 172, 254, 0.1)",
            borderWidth: 2,
            tension: 0.4,
            yAxisID: "y1",
          },
          {
            label: "Light (%)",
            data: [],
            borderColor: "#ffd93d",
            backgroundColor: "rgba(255, 217, 61, 0.1)",
            borderWidth: 2,
            tension: 0.4,
            yAxisID: "y1",
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
          mode: "index",
          intersect: false,
        },
        plugins: {
          legend: {
            display: true,
            labels: {
              color: "#a0a3bd",
            },
          },
        },
        scales: {
          x: {
            grid: {
              color: "#2a2d3a",
            },
            ticks: {
              color: "#a0a3bd",
            },
          },
          y: {
            type: "linear",
            display: true,
            position: "left",
            grid: {
              color: "#2a2d3a",
            },
            ticks: {
              color: "#a0a3bd",
            },
          },
          y1: {
            type: "linear",
            display: true,
            position: "right",
            grid: {
              drawOnChartArea: false,
            },
            ticks: {
              color: "#a0a3bd",
            },
          },
        },
      },
    });
  }
}

function getChartOptions(unit) {
  const theme = document.documentElement.getAttribute("data-theme") || "dark";
  const gridColor = theme === "light" ? "#e5e7eb" : "#2a2d3a";
  const textColor = theme === "light" ? "#6c757d" : "#a0a3bd";

  return {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        callbacks: {
          label: function (context) {
            return context.parsed.y.toFixed(1) + unit;
          },
        },
        backgroundColor:
          theme === "light" ? "rgba(0, 0, 0, 0.8)" : "rgba(30, 33, 48, 0.9)",
        titleColor: "#ffffff",
        bodyColor: "#ffffff",
      },
    },
    scales: {
      x: {
        display: false,
      },
      y: {
        display: false,
        beginAtZero: false,
      },
    },
  };
}

function updateCharts() {
  if (!state.stats) return;

  const now = new Date().toLocaleTimeString();

  // Update individual metric charts
  updateChart(tempChart, now, state.stats.temperature.average || 0);
  updateChart(humidityChart, now, state.stats.humidity.average || 0);
  updateChart(lightChart, now, state.stats.light.average || 0);

  // Update historical chart
  if (historicalChart) {
    historicalChart.data.labels.push(now);
    historicalChart.data.datasets[0].data.push(
      state.stats.temperature.average || 0
    );
    historicalChart.data.datasets[1].data.push(
      state.stats.humidity.average || 0
    );
    historicalChart.data.datasets[2].data.push(state.stats.light.average || 0);

    // Keep only last 20 data points
    if (historicalChart.data.labels.length > CONFIG.maxChartPoints) {
      historicalChart.data.labels.shift();
      historicalChart.data.datasets.forEach((dataset) => dataset.data.shift());
    }

    historicalChart.update("none");
  }
}

function updateChart(chart, label, value) {
  if (!chart) return;

  chart.data.labels.push(label);
  chart.data.datasets[0].data.push(value);

  // Keep only last 10 data points
  if (chart.data.labels.length > 10) {
    chart.data.labels.shift();
    chart.data.datasets[0].data.shift();
  }

  chart.update("none");
}

// ============================================
// Event Listeners
// ============================================

function setupEventListeners() {
  // Theme toggle button
  const themeToggle = document.getElementById("theme-toggle");
  if (themeToggle) {
    themeToggle.addEventListener("click", toggleTheme);
  }

  // Refresh devices button
  const refreshBtn = document.getElementById("refresh-devices");
  if (refreshBtn) {
    refreshBtn.addEventListener("click", () => {
      console.log("🔄 Refreshing devices...");
      loadDevices();
      showNotification("Refreshing devices...", "info");
    });
  }

  // Control mode radio buttons
  const controlModeInputs = document.querySelectorAll(
    'input[name="control-mode"]'
  );
  controlModeInputs.forEach((input) => {
    input.addEventListener("change", (e) => {
      state.controlMode = e.target.value;
      console.log(
        `🎛️ Control mode changed to: ${state.controlMode.toUpperCase()}`
      );
      showNotification(
        `Control mode: ${state.controlMode.toUpperCase()}`,
        "info"
      );
    });
  });

  // Navigation links
  const navLinks = document.querySelectorAll(".nav-link");
  navLinks.forEach((link) => {
    link.addEventListener("click", (e) => {
      e.preventDefault();

      // Update active state
      navLinks.forEach((l) => l.classList.remove("active"));
      link.classList.add("active");

      // Scroll to section
      const targetId = link.getAttribute("href").substring(1);
      const targetSection = document.getElementById(targetId);
      if (targetSection) {
        targetSection.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    });
  });

  // Heater indicators click
  const heaterIndicators = document.querySelectorAll(".heater-indicator");
  heaterIndicators.forEach((indicator) => {
    indicator.addEventListener("click", () => {
      const deviceId = parseInt(indicator.getAttribute("data-device"));
      toggleHeater(deviceId);
    });
  });
}

// ============================================
// Data Updates
// ============================================

function startDataUpdates() {
  // Initial load
  loadDevices();
  loadStats();

  // Regular updates
  setInterval(() => {
    loadDevices();
    loadStats();
  }, CONFIG.updateInterval);

  setInterval(updateCharts, CONFIG.chartUpdateInterval);
}

// ============================================
// Utility Functions
// ============================================

function showNotification(message, type = "info") {
  console.log(`[${type.toUpperCase()}] ${message}`);
  // In a real implementation, this would show a toast notification
}

// ============================================
// Export for debugging
// ============================================

window.PoultryControl = {
  state,
  toggleHeater,
  loadDevices,
  loadStats,
  CONFIG,
};

console.log("💡 Debug interface available at: window.PoultryControl");
