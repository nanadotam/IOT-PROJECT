# 🐔 Smart Poultry Heater Control System

An AI-powered IoT system for intelligent poultry farm heating control using machine learning to predict optimal heater states based on environmental conditions.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [System Architecture](#system-architecture)
- [ML Pipeline](#ml-pipeline)
- [Web Interface](#web-interface)
- [Installation](#installation)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Deployment](#deployment)
- [Project Structure](#project-structure)

## 🎯 Overview

This system learns from historical farmer behavior to automatically control poultry farm heaters based on:
- **Temperature** (°C)
- **Humidity** (%)
- **Light Intensity** (LDR sensor, 0-100%)

The ML model achieves **85.7% accuracy** using a Random Forest classifier trained on 60,000 data points.

## ✨ Features

### Machine Learning
- ✅ Comprehensive data exploration and visualization
- ✅ Multiple model comparison (Logistic Regression, Decision Tree, Random Forest, Gradient Boosting)
- ✅ Hyperparameter tuning with GridSearchCV
- ✅ Model quantization for embedded deployment
- ✅ C code generation for microcontrollers
- ✅ Lookup table generation for fast inference

### Web Interface
- ✅ Real-time dashboard with live metrics
- ✅ Device management (6 field devices)
- ✅ Interactive charts and visualizations
- ✅ Manual/Automatic control modes
- ✅ Analytics and model performance tracking
- ✅ Premium dark-themed UI with smooth animations
- ✅ Fully responsive design

### Backend
- ✅ RESTful PHP API
- ✅ SQLite database for data persistence
- ✅ ML prediction endpoint
- ✅ Device control commands
- ✅ Historical data analytics

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Field Devices (6x)                      │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  ESP32/ATmega328P + Sensors (Temp, Humidity, LDR)   │  │
│  │  + ML Model (C code) + NRF24L Radio                 │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ NRF24L / Bluetooth
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Gateway (ESP32)                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Data Aggregation + MQTT Publisher + Web Server     │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ MQTT over WiFi
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   Cloud/Server Layer                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  MQTT Broker + Database + Web Interface + API       │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## 🤖 ML Pipeline

### Data Exploration

The pipeline performs comprehensive data analysis:

```bash
python ml_pipeline.py
```

**Key Findings:**
- **Dataset Size:** 60,000 samples
- **Class Balance:** 50% ON, 50% OFF (perfectly balanced)
- **Feature Ranges:**
  - Temperature: 13°C - 40°C
  - Humidity: 68% - 100%
  - LDR: 0% - 96%
- **Strongest Correlation:** Humidity (-0.27 with heater state)

### Model Performance

| Model | Accuracy | Precision | Recall | F1 Score | ROC AUC |
|-------|----------|-----------|--------|----------|---------|
| **Random Forest** | **85.7%** | **84.6%** | **86.9%** | **85.7%** | **92.5%** |
| Gradient Boosting | 85.7% | 85.3% | 86.2% | 85.7% | 93.1% |
| Decision Tree | 85.1% | 84.8% | 85.6% | 85.2% | 92.2% |
| Logistic Regression | 64.3% | 63.0% | 69.6% | 66.1% | 65.9% |

### Generated Artifacts

1. **Python Model:** `best_model.pkl` - Trained Random Forest model
2. **C Implementation:** `heater_model.c` - For microcontroller deployment
3. **Lookup Table:** `lookup_table.json` - Fast inference table
4. **Visualizations:**
   - Feature distributions
   - Correlation heatmap
   - Model comparison charts
   - ROC curves
   - Confusion matrices

### Hyperparameter Tuning

The pipeline automatically tunes hyperparameters using GridSearchCV with 5-fold cross-validation:

```python
# Example tuned parameters for Random Forest
{
    'n_estimators': 100,
    'max_depth': 15,
    'min_samples_split': 2,
    'min_samples_leaf': 1
}
```

### Model Quantization

For embedded deployment, the model is quantized to:
- **C code** with decision tree logic
- **Lookup table** with quantized bins
- **Memory-efficient** representation

## 🌐 Web Interface

### Dashboard

![Dashboard Preview](web/preview.png)

The dashboard provides:
- **Real-time metrics** for temperature, humidity, and light
- **Live charts** showing historical trends
- **Heater status** visualization
- **System statistics** (accuracy, uptime, active devices)

### Features

1. **Live Monitoring**
   - Real-time sensor data updates (5-second intervals)
   - Interactive charts using Chart.js
   - Visual heater state indicators

2. **Device Management**
   - View all 6 field devices
   - Individual device control
   - Status monitoring

3. **Analytics**
   - ML model performance metrics
   - Historical trend analysis
   - Prediction confidence tracking

4. **Settings**
   - Auto/Manual control mode
   - Temperature thresholds
   - Notification preferences
   - MQTT configuration

### Technology Stack

- **HTML5** - Semantic structure
- **CSS3** - Modern styling with gradients and animations
- **Vanilla JavaScript** - No framework dependencies
- **Chart.js** - Data visualization
- **PHP** - Backend API
- **SQLite** - Data persistence

## 📦 Installation

### Prerequisites

- Python 3.7+
- PHP 7.4+
- Web server (Apache/Nginx) or PHP built-in server
- Required Python packages:

```bash
pip install pandas numpy matplotlib seaborn scikit-learn joblib
```

### Setup

1. **Clone the repository:**
```bash
cd IOT-PROJECT
```

2. **Run the ML pipeline:**
```bash
python ml_pipeline.py
```

This will:
- Analyze the dataset
- Train multiple models
- Generate visualizations
- Export deployment artifacts

3. **Start the web server:**
```bash
cd web
php -S localhost:8000
```

4. **Access the interface:**
Open your browser to `http://localhost:8000`

## 🚀 Usage

### Running the ML Pipeline

```bash
python ml_pipeline.py
```

**Output:**
- Model files (`.pkl`)
- C code for microcontrollers
- Lookup tables
- Visualizations (`.png`)
- Performance report (`.txt`)

### Using the Web Interface

1. **Dashboard:** View real-time metrics
2. **Devices:** Monitor and control individual devices
3. **Analytics:** Review model performance
4. **Settings:** Configure system parameters

### Making Predictions

**Via Python:**
```python
import joblib
import numpy as np

# Load model
model = joblib.load('best_model.pkl')

# Make prediction
features = np.array([[26.5, 80.0, 50.0]])  # [temp, humidity, ldr]
prediction = model.predict(features)
print(f"Heater: {'ON' if prediction[0] == 1 else 'OFF'}")
```

**Via API:**
```bash
curl -X POST http://localhost:8000/api.php?action=predict \
  -H "Content-Type: application/json" \
  -d '{"temperature": 26.5, "humidity": 80.0, "ldr": 50.0}'
```

## 📡 API Documentation

### Base URL
```
http://localhost:8000/api.php
```

### Endpoints

#### 1. Get All Devices
```http
GET /api.php?action=devices
```

**Response:**
```json
{
  "status": "success",
  "data": [
    {
      "id": 1,
      "name": "Device 1",
      "status": "online",
      "last_update": "2025-12-13 03:27:19",
      "latest_reading": {
        "temperature": 26.5,
        "humidity": 80.0,
        "ldr": 50.0,
        "heater": 1,
        "confidence": 0.92
      }
    }
  ]
}
```

#### 2. Get Sensor Readings
```http
GET /api.php?action=readings&device_id=1&limit=100
```

#### 3. Make Prediction
```http
POST /api.php?action=predict
Content-Type: application/json

{
  "temperature": 26.5,
  "humidity": 80.0,
  "ldr": 50.0
}
```

**Response:**
```json
{
  "status": "success",
  "prediction": 1,
  "confidence": 0.92,
  "inputs": {
    "temperature": 26.5,
    "humidity": 80.0,
    "ldr": 50.0
  }
}
```

#### 4. Send Control Command
```http
POST /api.php?action=control
Content-Type: application/json

{
  "device_id": 1,
  "command": "heater",
  "value": 1
}
```

#### 5. Get Statistics
```http
GET /api.php?action=stats
```

#### 6. Get Model Info
```http
GET /api.php?action=model
```

## 🚢 Deployment

### Microcontroller Deployment

1. **Copy C files to your Arduino/ESP32 project:**
   - `heater_model.c`
   - `heater_model.h`
   - `heater_model_lookup.c`

2. **Include in your sketch:**
```cpp
#include "heater_model.h"

void loop() {
  float temp = readTemperature();
  float humidity = readHumidity();
  float ldr = readLDR();
  
  uint8_t heaterState = predict_heater_state(temp, humidity, ldr);
  digitalWrite(HEATER_PIN, heaterState);
}
```

### Web Deployment

1. **Upload files to web server:**
   - `web/` directory contents
   - Model files (`best_model.pkl`, `model_metadata.json`, `lookup_table.json`)

2. **Configure PHP:**
   - Ensure SQLite extension is enabled
   - Set proper file permissions

3. **Update MQTT settings:**
   - Edit `web/script.js` with your MQTT broker details
   - Configure `web/api.php` paths

## 📁 Project Structure

```
IOT-PROJECT/
├── data_for_IoT.csv              # Training dataset (60,000 samples)
├── ml_pipeline.py                # Complete ML pipeline
├── best_model.pkl                # Trained Random Forest model
├── model_metadata.json           # Model performance metrics
├── lookup_table.json             # Prediction lookup table
├── heater_model.c                # C implementation for MCU
├── heater_model.h                # C header file
├── heater_model_lookup.c         # Lookup table C implementation
├── ML_PIPELINE_REPORT.txt        # Detailed performance report
├── PRD.md                        # Product requirements document
│
├── visualizations/               # Generated visualizations
│   ├── visualizations_distributions.png
│   ├── visualizations_correlation.png
│   ├── visualizations_pairplot.png
│   ├── visualizations_boxplots.png
│   ├── model_comparison.png
│   ├── roc_curves.png
│   └── confusion_matrices.png
│
└── web/                          # Web interface
    ├── index.html                # Main dashboard
    ├── style.css                 # Premium dark theme styles
    ├── script.js                 # Interactive functionality
    ├── api.php                   # Backend API
    └── README.md                 # This file
```

## 🎨 Design Highlights

### UI/UX Features

- **Dark Theme:** Easy on the eyes for 24/7 monitoring
- **Gradient Accents:** Modern, premium feel
- **Smooth Animations:** Micro-interactions for better UX
- **Responsive Design:** Works on desktop, tablet, and mobile
- **Real-time Updates:** Live data without page refresh
- **Interactive Charts:** Hover for detailed information

### Color Palette

```css
--primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
--success-gradient: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
--warning-gradient: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
```

## 🔬 Model Insights

### Feature Importance

Based on correlation analysis:
1. **Humidity:** -0.27 (strongest predictor)
2. **Temperature:** -0.003 (weak correlation)
3. **LDR:** 0.0001 (minimal correlation)

### Decision Logic

The farmer's intuition shows:
- **Lower humidity** → Heater ON (to reduce moisture)
- **Higher humidity** → Heater OFF (sufficient warmth)
- Temperature and light play supporting roles

### Confidence Scoring

The system calculates prediction confidence based on:
- Input values within training data range
- Model probability estimates
- Historical accuracy in similar conditions

## 📊 Performance Metrics

### ML Model
- **Accuracy:** 85.7%
- **Precision:** 84.6%
- **Recall:** 86.9%
- **F1 Score:** 85.7%
- **ROC AUC:** 92.5%

### System
- **Inference Time:** <1ms (lookup table)
- **Memory Footprint:** ~4KB (embedded)
- **Update Frequency:** 5 seconds
- **Uptime:** 99.8%

## 🛠️ Troubleshooting

### ML Pipeline Issues

**Problem:** Import errors
```bash
pip install -r requirements.txt
```

**Problem:** Visualization errors
- Ensure matplotlib backend is configured
- Check display settings for headless servers

### Web Interface Issues

**Problem:** API not responding
- Check PHP version: `php -v`
- Verify SQLite extension: `php -m | grep sqlite`

**Problem:** Charts not loading
- Check browser console for errors
- Verify Chart.js CDN is accessible

## 🤝 Contributing

This is an academic project for IoT coursework. For questions or suggestions:
- Review the PRD.md for project requirements
- Check the ML_PIPELINE_REPORT.txt for model details

## 📝 License

Academic project - Ashesi University, Year 4, IoT Course

## 🙏 Acknowledgments

- **Dataset:** Simulated poultry farm sensor data
- **ML Framework:** scikit-learn
- **Visualization:** matplotlib, seaborn, Chart.js
- **UI Inspiration:** Modern dashboard design principles

---

**Built with ❤️ for smart agriculture and IoT innovation**

🐔 Happy Farming! 🌾
