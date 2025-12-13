# 📄 PRODUCT REQUIREMENTS DOCUMENT (PRD)

## 1. Product Overview

**Product name (working):** Smart Poultry Heater Control System

**Problem Statement**
An experienced poultry farmer controls heating based on intuition using temperature, humidity, and light. This intuition is not rule-based and cannot be written as deterministic logic. The goal is to **learn this behavior from historical data**, deploy it on **resource-constrained microcontrollers**, and scale it across a large poultry farm with centralized monitoring and control.

**Primary Objective**
Develop, deploy, and test a **machine learning–based heater control system** that:

* Learns when to turn the heater ON/OFF
* Runs on a microcontroller
* Scales to multiple sensor nodes
* Publishes data to a central system for monitoring and control

---

## 2. Users & Stakeholders

* **Primary user:** Poultry farmer
* **Secondary users:** Farm supervisors, technicians
* **Technical stakeholders:** IoT developers, ML engineers, system integrators
* **Hardware stakeholders:** ESP32 / ATmega328P field device operators

---

## 3. Data Inputs and Outputs

### Input Features (from CSV)

Based on the attached dataset:

* `Temp` (Temperature)
* `Humidity`
* `LDR` (Light intensity mapped to 0–100)

### Output Label

* `Heater`

  * `1` = Heater ON
  * `0` = Heater OFF

### Dataset Size

* ~60,000 rows
* Supervised binary classification

---

## 4. Functional Requirements

### Part A: Machine Learning System

**FR-A1: Data Analysis**

* Analyze correlations between temperature, humidity, light, and heater state
* Identify missing or under-represented ranges

**FR-A2: Model Development**

* Train a supervised ML model to predict heater ON/OFF
* Use a suitable accuracy metric (accuracy, precision, recall, or F1)

**FR-A3: Human Override Detection**

* Detect out-of-distribution inputs
* Flag cases where prediction confidence is low and a human override is required

**FR-A4: Embedded Model Constraint**

* Model must fit on a microcontroller
* Prefer lightweight models (Decision Tree, Logistic Regression, TinyML NN)

**FR-A5: Synthetic Testing**

* Hard-code 3–5 test parameter sets
* Print or actuate predicted heater state

**FR-A6 (Extra Credit): Live Sensor Testing**

* Read temperature, humidity, and LDR sensors
* Predict output
* Activate LED or lamp accordingly

---

### Part B: Distributed IoT System

**FR-B1: Field Devices**

* 3–6 sensor nodes using ESP32 or ATmega328P
* Sensors: temperature, humidity, LDR
* Communication via NRF24L (or Bluetooth)

**FR-B2: Gateway Node**

* Central ESP32 gateway
* Receives data from field devices
* Publishes data to MQTT broker over Wi-Fi

**FR-B3: Data Persistence**

* Python script subscribes to MQTT topics
* Stores data in a database (gateway does NOT write to DB)

**FR-B4: Web Control Interface**

* Gateway ESP32 hosts a web page
* User can:

  * View connected devices
  * Send ON/OFF commands to specific field devices

---

## 5. Non-Functional Requirements

* **Latency:** Near real-time sensor updates
* **Reliability:** NRF24L packet retry handling
* **Scalability:** Support at least 6 field devices
* **Resource constraints:**

  * Low RAM
  * Low flash
  * No floating-point heavy inference
* **Explainability:** Model behavior should be interpretable

---

## 6. Assumptions & Constraints

* Not all sensor ranges are covered in training data
* LDR values must be normalized to 0–100
* ESP32 gateway handles networking and UI
* Field devices are computation-limited
* Team size: 4, all members understand entire system

---

## 7. Success Metrics

* ML prediction accuracy ≥ chosen baseline
* Model compiles and runs on microcontroller
* Successful synthetic tests
* End-to-end data flow:

  * Field device → Gateway → MQTT → Database
* Remote device control via web interface

---

# 🧩 SPRINT BREAKDOWN (1-Week Project)

## 🟦 Sprint 1: Data & ML Foundations (Days 1–2)

**Goals**

* Understand farmer behavior via data
* Build first working model

**Tasks**

* Explore CSV data distributions
* Feature scaling and preprocessing
* Train baseline classifier
* Evaluate accuracy and confusion matrix
* Identify uncertain regions for override

**Deliverables**

* Trained ML model
* Accuracy results
* Feature importance insights

---

## 🟦 Sprint 2: Embedded Model & Device Testing (Days 3–4)

**Goals**

* Run ML logic on microcontroller
* Validate predictions without sensors

**Tasks**

* Convert model to embedded-friendly format
* Implement inference logic in ESP32/ATmega code
* Hard-code 3–5 synthetic test cases
* Activate LED based on prediction

**Deliverables**

* Microcontroller-compatible model
* Serial output showing predictions
* LED/Lamp activation proof

---

## 🟦 Sprint 3: Multi-Node Communication (Day 5)

**Goals**

* Enable distributed sensing

**Tasks**

* Configure NRF24L communication
* Transmit sensor data from 3+ nodes
* Gateway receives and parses payloads

**Deliverables**

* Stable RF communication
* Multi-node data aggregation

---

## 🟦 Sprint 4: Gateway, MQTT & Database (Day 6)

**Goals**

* Centralize and persist data

**Tasks**

* Gateway publishes data to MQTT topics
* Python MQTT subscriber script
* Store messages in database

**Deliverables**

* Live MQTT stream
* Database records populated

---

## 🟦 Sprint 5: Web Control & Integration (Day 7)

**Goals**

* Close the loop with user control

**Tasks**

* ESP32 web server
* Device selection UI
* ON/OFF command dispatch to field nodes

**Deliverables**

* Web interface demo
* Remote control of field device LEDs

---

## 8. Optional Creative Extensions (Bonus)

* Confidence score display
* Visual dashboard
* Alert when override is required
* Adaptive learning or retraining trigger

---