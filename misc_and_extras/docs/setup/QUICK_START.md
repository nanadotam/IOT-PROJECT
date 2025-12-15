# 🚀 Quick Start Guide

## Smart Poultry Heater Control System

Get up and running in 5 minutes!

---

## 📋 Prerequisites

- Python 3.7+ installed
- Web browser (Chrome, Firefox, Safari, Edge)
- Terminal/Command Prompt access

---

## ⚡ Quick Start

### Step 1: View ML Results

The ML pipeline has already been run! Check the results:

```bash
# View the summary report
cat ML_PIPELINE_REPORT.txt

# Or open it in your text editor
open ML_PIPELINE_REPORT.txt
```

**Key Results:**
- ✅ **Best Model:** Random Forest
- ✅ **Accuracy:** 85.7%
- ✅ **F1 Score:** 85.7%
- ✅ **ROC AUC:** 92.5%

### Step 2: View Visualizations

Open the generated visualization files:

```bash
# Open all visualizations
open visualizations_*.png
open model_comparison.png
open roc_curves.png
open confusion_matrices.png
```

**Generated Charts:**
- 📊 Feature distributions
- 🔗 Correlation heatmap
- 📈 Model comparison
- 📉 ROC curves
- 🎯 Confusion matrices

### Step 3: Launch Web Interface

Open the web interface in your browser:

**Option A: Direct File Access**
```bash
# macOS
open web/index.html

# Windows
start web/index.html

# Linux
xdg-open web/index.html
```

**Option B: Local Server (Recommended)**
```bash
# Navigate to web directory
cd web

# Start PHP server
php -S localhost:8000

# Open browser to http://localhost:8000
```

### Step 4: Explore the Dashboard

The web interface includes:

1. **📊 Live Dashboard**
   - Real-time sensor metrics
   - Interactive charts
   - Heater status indicators

2. **🔧 Device Management**
   - 6 field devices
   - Individual controls
   - Status monitoring

3. **📈 Analytics**
   - ML model performance
   - Historical trends
   - Confidence tracking

4. **⚙️ Settings**
   - Auto/Manual modes
   - Thresholds
   - Notifications

---

## 🔬 Re-run ML Pipeline (Optional)

If you want to re-run the ML pipeline:

```bash
# Make sure you're in the project directory
cd IOT-PROJECT

# Run the pipeline
python ml_pipeline.py
```

This will:
- ✅ Analyze the dataset
- ✅ Train 4 different models
- ✅ Generate visualizations
- ✅ Export deployment artifacts
- ✅ Create C code for microcontrollers

**Time:** ~2-3 minutes

---

## 📊 View Model Metadata

```bash
# View model information
cat model_metadata.json

# Pretty print JSON
python -m json.tool model_metadata.json
```

**Output:**
```json
{
  "model_name": "Random Forest",
  "features": ["Temp", "Humidity", "LDR"],
  "target": "Heater",
  "performance": {
    "accuracy": 0.8573,
    "precision": 0.8458,
    "recall": 0.8692,
    "f1_score": 0.8573,
    "roc_auc": 0.9252
  }
}
```

---

## 🧪 Test ML Predictions

### Using Python

```python
import joblib
import numpy as np

# Load the model
model = joblib.load('best_model.pkl')

# Test prediction
temp = 26.5      # Temperature in °C
humidity = 80.0  # Humidity in %
ldr = 50.0       # Light intensity (0-100)

features = np.array([[temp, humidity, ldr]])
prediction = model.predict(features)

print(f"Temperature: {temp}°C")
print(f"Humidity: {humidity}%")
print(f"Light: {ldr}%")
print(f"Heater: {'ON' if prediction[0] == 1 else 'OFF'}")
```

### Using the API

```bash
# Start the PHP server first
cd web
php -S localhost:8000

# In another terminal, make a prediction
curl -X POST http://localhost:8000/api.php?action=predict \
  -H "Content-Type: application/json" \
  -d '{"temperature": 26.5, "humidity": 80.0, "ldr": 50.0}'
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

---

## 📁 Project Structure

```
IOT-PROJECT/
├── 📊 ML Files
│   ├── ml_pipeline.py          ← Main ML script
│   ├── best_model.pkl          ← Trained model
│   ├── model_metadata.json     ← Model info
│   └── ML_PIPELINE_REPORT.txt  ← Results
│
├── 📈 Visualizations
│   ├── visualizations_*.png    ← Data analysis
│   ├── model_comparison.png    ← Model results
│   └── confusion_matrices.png  ← Accuracy metrics
│
├── 🌐 Web Interface
│   └── web/
│       ├── index.html          ← Dashboard
│       ├── style.css           ← Styling
│       ├── script.js           ← Interactivity
│       └── api.php             ← Backend
│
├── 🔧 Deployment
│   ├── heater_model.c          ← C code for MCU
│   ├── heater_model.h          ← Header file
│   └── heater_model_lookup.c   ← Lookup table
│
└── 📚 Documentation
    ├── README.md               ← Full documentation
    ├── PROJECT_SUMMARY.md      ← Completion summary
    └── QUICK_START.md          ← This file
```

---

## 🎯 Common Tasks

### View All Generated Files

```bash
ls -lh *.png *.pkl *.json *.txt *.c *.h
```

### Check Model Size

```bash
du -h best_model.pkl
# Output: 13.8M
```

### View Dataset Info

```bash
wc -l data_for_IoT.csv
# Output: 60000 lines
```

### Test Web Interface Locally

```bash
cd web
python3 -m http.server 8000
# Or
php -S localhost:8000
```

---

## 🐛 Troubleshooting

### Issue: Python packages not found

```bash
pip install pandas numpy matplotlib seaborn scikit-learn joblib
```

### Issue: Web interface not loading

1. Check if you're in the `web/` directory
2. Try a different port: `php -S localhost:8080`
3. Open directly: `open index.html`

### Issue: Charts not showing

1. Check internet connection (Chart.js CDN)
2. Open browser console (F12) for errors
3. Try a different browser

### Issue: API not responding

1. Ensure PHP is installed: `php -v`
2. Check SQLite extension: `php -m | grep sqlite`
3. Verify file permissions

---

## 📖 Next Steps

1. **Explore the Dashboard**
   - Try different control modes
   - View analytics
   - Check device status

2. **Review ML Results**
   - Study the visualizations
   - Understand model performance
   - Check feature importance

3. **Read Full Documentation**
   - Open `README.md` for complete guide
   - Check `PROJECT_SUMMARY.md` for overview
   - Review `PRD.md` for requirements

4. **Deploy to Hardware**
   - Use `heater_model.c` for ESP32
   - Configure MQTT broker
   - Set up field devices

---

## 🎓 Learning Resources

### Understanding the ML Model

- **Random Forest:** Ensemble of decision trees
- **Features:** Temperature, Humidity, Light
- **Target:** Heater ON/OFF (binary classification)
- **Accuracy:** 85.7% (very good for real-world data)

### Key Insights

1. **Humidity is the strongest predictor** (-0.27 correlation)
2. **Lower humidity → Heater ON** (farmer's intuition)
3. **Model is well-balanced** (similar precision and recall)
4. **High confidence** (92.5% ROC AUC)

---

## 💡 Tips

- 🔄 **Refresh the dashboard** to see live data updates
- 📊 **Hover over charts** for detailed values
- 🎛️ **Switch to manual mode** to control heaters
- 📈 **Check analytics** for model insights
- ⚙️ **Adjust settings** for custom thresholds

---

## 🆘 Need Help?

1. **Check the README:** `README.md`
2. **View the summary:** `PROJECT_SUMMARY.md`
3. **Read the report:** `ML_PIPELINE_REPORT.txt`
4. **Inspect the code:** All files are well-commented

---

## ✅ Success Checklist

- [ ] ML pipeline results viewed
- [ ] Visualizations opened
- [ ] Web interface launched
- [ ] Dashboard explored
- [ ] Model predictions tested
- [ ] Documentation reviewed

---

**🎉 You're all set! Enjoy exploring the Smart Poultry Heater Control System!**

🐔 Happy Farming! 🌾
