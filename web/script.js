/**
 * Smart Poultry Heater Control System - JavaScript
 * Handles real-time data updates, device control, and visualizations
 */

// ============================================
// Configuration
// ============================================

const CONFIG = {
  updateInterval: 5000, // 5 seconds
  mqttBroker: "192.168.1.100",
  mqttPort: 1883,
  deviceCount: 6,
  chartUpdateInterval: 10000, // 10 seconds
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
};

// ============================================
// Device Data Generator (Simulated)
// ============================================

function generateDeviceData(deviceId) {
  // Simulate realistic sensor readings based on the dataset
  const temp = 18 + Math.random() * 20; // 18-38°C
  const humidity = 70 + Math.random() * 30; // 70-100%
  const ldr = Math.random() * 96; // 0-96%

  // Simple ML prediction simulation (based on humidity correlation)
  const heaterPrediction = humidity < 80 ? 1 : Math.random() > 0.5 ? 1 : 0;

  return {
    id: deviceId,
    name: `Device ${deviceId}`,
    status: "online",
    temperature: parseFloat(temp.toFixed(1)),
    humidity: parseFloat(humidity.toFixed(1)),
    ldr: parseFloat(ldr.toFixed(1)),
    heater: heaterPrediction,
    lastUpdate: new Date().toISOString(),
    confidence: 85 + Math.random() * 10, // 85-95%
  };
}

// ============================================
// Initialize Application
// ============================================

document.addEventListener("DOMContentLoaded", () => {
  console.log("🚀 Initializing Smart Poultry Heater Control System...");

  initializeTheme();
  initializeDevices();
  initializeCharts();
  setupEventListeners();
  startDataUpdates();

  console.log("✅ System initialized successfully!");
});

// ============================================
// Theme Management
// ============================================

function initializeTheme() {
  // Check for saved theme preference or default to 'dark'
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

function initializeDevices() {
  state.devices = [];
  for (let i = 1; i <= CONFIG.deviceCount; i++) {
    state.devices.push(generateDeviceData(i));
  }
  renderDevices();
  updateDashboardMetrics();
}

function renderDevices() {
  const container = document.getElementById("devices-container");
  if (!container) return;

  container.innerHTML = "";

  state.devices.forEach((device) => {
    const deviceCard = createDeviceCard(device);
    container.appendChild(deviceCard);
  });
}

function createDeviceCard(device) {
  const card = document.createElement("div");
  card.className = "device-card";
  card.setAttribute("data-device-id", device.id);

  card.innerHTML = `
        <div class="device-header">
            <h3 class="device-name">${device.name}</h3>
            <span class="device-status ${device.status}">${device.status}</span>
        </div>
        
        <div class="device-readings">
            <div class="device-reading">
                <div class="reading-label">Temperature</div>
                <div class="reading-value">
                    ${device.temperature}
                    <span class="reading-unit">°C</span>
                </div>
            </div>
            <div class="device-reading">
                <div class="reading-label">Humidity</div>
                <div class="reading-value">
                    ${device.humidity}
                    <span class="reading-unit">%</span>
                </div>
            </div>
            <div class="device-reading">
                <div class="reading-label">Light</div>
                <div class="reading-value">
                    ${device.ldr}
                    <span class="reading-unit">%</span>
                </div>
            </div>
        </div>
        
        <div class="device-controls">
            <button class="btn ${device.heater ? "btn-danger" : "btn-success"}" 
                    onclick="toggleHeater(${device.id})">
                <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                          d="M17.657 18.657A8 8 0 016.343 7.343S7 9 9 10c0-2 .5-5 2.986-7C14 5 16.09 5.777 17.656 7.343A7.975 7.975 0 0120 13a7.975 7.975 0 01-2.343 5.657z" />
                </svg>
                Heater ${device.heater ? "ON" : "OFF"}
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
    `;

  return card;
}

function toggleHeater(deviceId) {
  const device = state.devices.find((d) => d.id === deviceId);
  if (!device) return;

  if (state.controlMode === "auto") {
    alert(
      "⚠️ System is in AUTO mode. Switch to MANUAL mode to control heaters manually."
    );
    return;
  }

  device.heater = device.heater ? 0 : 1;
  renderDevices();
  updateDashboardMetrics();

  console.log(
    `🔥 Device ${deviceId} heater toggled to ${device.heater ? "ON" : "OFF"}`
  );
}

function viewDeviceDetails(deviceId) {
  const device = state.devices.find((d) => d.id === deviceId);
  if (!device) return;

  alert(
    `📊 Device ${deviceId} Details\n\n` +
      `Status: ${device.status}\n` +
      `Temperature: ${device.temperature}°C\n` +
      `Humidity: ${device.humidity}%\n` +
      `Light: ${device.ldr}%\n` +
      `Heater: ${device.heater ? "ON" : "OFF"}\n` +
      `Confidence: ${device.confidence.toFixed(1)}%\n` +
      `Last Update: ${new Date(device.lastUpdate).toLocaleString()}`
  );
}

// ============================================
// Dashboard Metrics
// ============================================

function updateDashboardMetrics() {
  // Calculate averages
  const avgTemp =
    state.devices.reduce((sum, d) => sum + d.temperature, 0) /
    state.devices.length;
  const avgHumidity =
    state.devices.reduce((sum, d) => sum + d.humidity, 0) /
    state.devices.length;
  const avgLight =
    state.devices.reduce((sum, d) => sum + d.ldr, 0) / state.devices.length;
  const heatersOn = state.devices.filter((d) => d.heater === 1).length;

  // Update dashboard
  updateElement("avg-temp", avgTemp.toFixed(1));
  updateElement("avg-humidity", avgHumidity.toFixed(1));
  updateElement("avg-light", avgLight.toFixed(1));
  updateElement("heaters-on", heatersOn);
  updateElement(
    "heater-percentage",
    `${((heatersOn / CONFIG.deviceCount) * 100).toFixed(0)}%`
  );

  // Update heater indicators
  const indicators = document.querySelectorAll(".heater-indicator");
  indicators.forEach((indicator, index) => {
    const device = state.devices[index];
    if (device) {
      indicator.className = `heater-indicator ${device.heater ? "on" : "off"}`;
    }
  });

  // Update confidence gauge
  const avgConfidence =
    state.devices.reduce((sum, d) => sum + d.confidence, 0) /
    state.devices.length;
  updateElement("confidence-value", Math.round(avgConfidence));
  updateConfidenceGauge(avgConfidence);
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
  const now = new Date().toLocaleTimeString();

  // Calculate current averages
  const avgTemp =
    state.devices.reduce((sum, d) => sum + d.temperature, 0) /
    state.devices.length;
  const avgHumidity =
    state.devices.reduce((sum, d) => sum + d.humidity, 0) /
    state.devices.length;
  const avgLight =
    state.devices.reduce((sum, d) => sum + d.ldr, 0) / state.devices.length;

  // Update individual metric charts
  updateChart(tempChart, now, avgTemp);
  updateChart(humidityChart, now, avgHumidity);
  updateChart(lightChart, now, avgLight);

  // Update historical chart
  if (historicalChart) {
    historicalChart.data.labels.push(now);
    historicalChart.data.datasets[0].data.push(avgTemp);
    historicalChart.data.datasets[1].data.push(avgHumidity);
    historicalChart.data.datasets[2].data.push(avgLight);

    // Keep only last 20 data points
    if (historicalChart.data.labels.length > 20) {
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
      updateDevices();
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

      if (state.controlMode === "auto") {
        // Re-apply ML predictions
        updateDevices();
      }
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
  // Initial update
  updateDevices();
  updateCharts();

  // Regular updates
  setInterval(updateDevices, CONFIG.updateInterval);
  setInterval(updateCharts, CONFIG.chartUpdateInterval);
}

function updateDevices() {
  // Simulate receiving new data from devices
  state.devices = state.devices.map((device) => {
    const newData = generateDeviceData(device.id);

    // In auto mode, use ML prediction
    if (state.controlMode === "auto") {
      return newData;
    } else {
      // In manual mode, keep current heater state
      return { ...newData, heater: device.heater };
    }
  });

  renderDevices();
  updateDashboardMetrics();
}

// ============================================
// Utility Functions
// ============================================

function formatTimestamp(timestamp) {
  const date = new Date(timestamp);
  return date.toLocaleString();
}

function showNotification(message, type = "info") {
  console.log(`[${type.toUpperCase()}] ${message}`);
  // In a real implementation, this would show a toast notification
}

// ============================================
// MQTT Integration (Placeholder)
// ============================================

function connectMQTT() {
  // This would connect to the actual MQTT broker
  // For now, we're using simulated data
  console.log("📡 MQTT connection would be established here");
  state.isConnected = true;
}

function publishMQTT(topic, message) {
  console.log(`📤 Publishing to ${topic}:`, message);
  // Actual MQTT publish would happen here
}

function subscribeMQTT(topic) {
  console.log(`📥 Subscribing to ${topic}`);
  // Actual MQTT subscribe would happen here
}

// ============================================
// Export for debugging
// ============================================

window.PoultryControl = {
  state,
  toggleHeater,
  updateDevices,
  connectMQTT,
  CONFIG,
};

console.log("💡 Debug interface available at: window.PoultryControl");
