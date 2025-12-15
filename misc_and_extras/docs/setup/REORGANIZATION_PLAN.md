# Repository Reorganization Plan

## New Structure

```
IOT-PROJECT/
├── README.md                          # Main project README
├── requirements.txt                   # Python dependencies
├── .gitignore                         # Git ignore file
├── .venv/                             # Virtual environment (keep)
│
├── docs/                              # 📚 All Documentation
│   ├── setup/
│   │   ├── SETUP_GUIDE.md
│   │   ├── QUICK_START.md
│   │   └── WEB_QUICK_START.md
│   ├── architecture/
│   │   ├── SYSTEM_ARCHITECTURE.md
│   │   ├── MQTT_DATABASE_ARCHITECTURE.md
│   │   └── PROJECT_SUMMARY.md
│   ├── mqtt/
│   │   ├── MQTT_BRIDGE_SUMMARY.md
│   │   └── MQTT_QUICK_REFERENCE.md
│   ├── web/
│   │   ├── WEB_UPDATE_SUMMARY.md
│   │   └── WEB_README.md
│   ├── ml/
│   │   └── ML_PIPELINE_REPORT.txt
│   └── PRD.md
│
├── src/                               # 💻 Source Code
│   ├── mqtt/
│   │   ├── mqtt_bridge_mysql.py      # Main MQTT bridge
│   │   ├── mqtt_bridge.py            # Legacy bridge
│   │   ├── test_mqtt_publisher.py    # Test publisher
│   │   └── config.py                 # MQTT configuration
│   ├── ml/
│   │   ├── ml_pipeline.py            # ML training pipeline
│   │   └── ML_Pipeline_Notebook.ipynb
│   └── embedded/
│       └── heater_model_lookup.c     # C code for embedded
│
├── web/                               # 🌐 Web Interface
│   ├── index.html
│   ├── style.css
│   ├── script.js
│   ├── api.php
│   ├── test_api.html
│   └── README.md
│
├── database/                          # 🗄️ Database Files
│   └── database_setup.sql
│
├── data/                              # 📊 Data Files
│   ├── raw/
│   │   └── data_for_IoT.csv
│   └── processed/
│       └── lookup_table.json
│
├── models/                            # 🤖 ML Models
│   ├── best_model.pkl
│   └── model_metadata.json
│
├── assets/                            # 🎨 Images & Assets
│   ├── visualizations/
│   │   ├── visualizations_boxplots.png
│   │   ├── visualizations_correlation.png
│   │   ├── visualizations_distributions.png
│   │   └── visualizations_pairplot.png
│   ├── model_performance/
│   │   ├── confusion_matrices.png
│   │   ├── model_comparison.png
│   │   └── roc_curves.png
│   └── project/
│       └── IoT_final_project25_3.pdf
│
└── logs/                              # 📝 Log Files
    └── mqtt_bridge.log
```

## Files to Move

### Documentation → docs/
- SETUP_GUIDE.md → docs/setup/
- QUICK_START.md → docs/setup/
- WEB_QUICK_START.md → docs/setup/
- SYSTEM_ARCHITECTURE.md → docs/architecture/
- MQTT_DATABASE_ARCHITECTURE.md → docs/architecture/
- PROJECT_SUMMARY.md → docs/architecture/
- MQTT_BRIDGE_SUMMARY.md → docs/mqtt/
- MQTT_QUICK_REFERENCE.md → docs/mqtt/
- WEB_UPDATE_SUMMARY.md → docs/web/
- web/README.md → docs/web/WEB_README.md
- ML_PIPELINE_REPORT.txt → docs/ml/
- PRD.md → docs/

### Source Code → src/
- mqtt_bridge_mysql.py → src/mqtt/
- mqtt_bridge.py → src/mqtt/
- test_mqtt_publisher.py → src/mqtt/
- config.py → src/mqtt/
- ml_pipeline.py → src/ml/
- ML_Pipeline_Notebook.ipynb → src/ml/
- heater_model_lookup.c → src/embedded/

### Database → database/
- database_setup.sql → database/

### Data → data/
- data_for_IoT.csv → data/raw/
- lookup_table.json → data/processed/

### Models → models/
- best_model.pkl → models/
- model_metadata.json → models/

### Assets → assets/
- All PNG files → assets/visualizations/ or assets/model_performance/
- PDF → assets/project/

### Logs → logs/
- mqtt_bridge.log → logs/

### Web (stays as is)
- web/ → web/ (no change)
