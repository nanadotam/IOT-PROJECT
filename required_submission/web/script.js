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
  controlMode: localStorage.getItem("controlMode") || "auto",
  isConnected: false,
  stats: null,
  autoRefreshInterval: null,
  chartUpdateInterval: null,
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
  initializeControlMode();
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

function initializeControlMode() {
  const savedMode = state.controlMode;
  const radioButton = document.querySelector(
    `input[name="control-mode"][value="${savedMode}"]`
  );

  if (radioButton) {
    radioButton.checked = true;
  }

  console.log(`🎛️ Control mode initialized: ${savedMode.toUpperCase()}`);
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

  // Format timestamp
  let timeAgo = "No data";
  if (reading.timestamp) {
    const timestamp = new Date(reading.timestamp);
    const now = new Date();
    const secondsAgo = Math.floor((now - timestamp) / 1000);

    if (secondsAgo < 60) {
      timeAgo = `${secondsAgo}s ago`;
    } else if (secondsAgo < 3600) {
      timeAgo = `${Math.floor(secondsAgo / 60)}m ago`;
    } else {
      timeAgo = timestamp.toLocaleTimeString();
    }
  }

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
      
      <div class="device-footer">
        <div class="device-timestamp">
          <span>Last updated: ${timeAgo}</span>
        </div>
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

  // Update average temperature stat card in hero section
  const avgTempStat = document.getElementById("avg-temp-stat");
  if (avgTempStat && state.stats.temperature.average) {
    avgTempStat.textContent = `${state.stats.temperature.average}°C`;
  }
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
}

// ============================================
// Data Updates
// ============================================

function startDataUpdates() {
  // Initial load
  loadDevices();
  loadStats();

  // Regular updates
  state.autoRefreshInterval = setInterval(() => {
    loadDevices();
    loadStats();
  }, CONFIG.updateInterval);

  state.chartUpdateInterval = setInterval(
    updateCharts,
    CONFIG.chartUpdateInterval
  );
}

function pauseAutoRefresh() {
  if (state.autoRefreshInterval) {
    clearInterval(state.autoRefreshInterval);
    state.autoRefreshInterval = null;
    console.log("⏸️ Auto-refresh paused");
  }
  if (state.chartUpdateInterval) {
    clearInterval(state.chartUpdateInterval);
    state.chartUpdateInterval = null;
  }
}

function resumeAutoRefresh() {
  // Clear any existing intervals first
  pauseAutoRefresh();

  // Start new intervals
  state.autoRefreshInterval = setInterval(() => {
    loadDevices();
    loadStats();
  }, CONFIG.updateInterval);

  state.chartUpdateInterval = setInterval(
    updateCharts,
    CONFIG.chartUpdateInterval
  );

  console.log("▶️ Auto-refresh resumed");

  // Immediate refresh
  loadDevices();
  loadStats();
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
  loadDevices,
  loadStats,
  CONFIG,
};

console.log("Debug interface available at: window.PoultryControl");
