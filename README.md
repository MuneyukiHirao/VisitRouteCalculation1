# VRP Scheduling and Routing with OR-Tools

This repository contains a set of Python modules designed for solving vehicle routing and scheduling problems (VRP) with time windows, using [Google OR-Tools](https://developers.google.com/optimization) as the core solver. The primary purpose is to generate multi-day visit plans for multiple targets (with latitude/longitude coordinates), taking into account work schedules, holidays, mandatory visits, exact visit times, and potential use of external APIs (Google Maps Directions) or fallback distance calculations.

---

## Overview

1. **Purpose**  
   - **Generate routing schedules** for up to 100 targets (by default) spread across Cebu Island in the Philippines, or any arbitrary locations.
   - **Assign visits** to one or more vehicles (or persons) while respecting daily time windows (e.g., 8:00–19:00) and holidays/weekends.
   - **Handle mandatory targets** that must be visited, and optional targets that may be skipped with a penalty.
   - **Support exact visit time** constraints when certain appointments are fixed (e.g., must arrive at 10:30).

2. **Core Functionality**  
   - **Distance Calculation**: 
     - By default uses the Haversine formula plus a customizable average driving speed factor.
     - Optionally can call the Google Maps Directions API to get driving times (if an API key is provided).
   - **Multi-Day Scheduling**:
     - Each vehicle has a list of available days; holidays or weekends are excluded or set to `None`.
     - Internally, days are mapped to "virtual vehicles" so that OR-Tools can handle them in a single pass.
   - **Recalculation / Incremental Updates**:
     - If new appointment targets are added or conditions change, the solution can be recalculated using the previous assignment as a hint.

3. **Program Structure**

   The main modules are as follows:
   - **`data_provider.py`**  
     Provides functions to load branch (depot) info and targets from CSV or JSON.
   - **`branch_loader.py`**  
     Loads branch (depot) information (ID, latitude, longitude) from a CSV file-like object.
   - **`targets_loader.py`**  
     Loads a list of targets from CSV, including their ID, latitude/longitude, and stay duration.
   - **`time_management.py`**  
     Manages date ranges, daily start/end windows, holiday checks, and conversion between datetime and minutes.
   - **`schedule_to_vehicles.py`**  
     Converts each (vehicle × day) combination to a "virtual vehicle" for the VRP model.
   - **`distance_loader.py`**  
     Implements the Haversine distance calculation and optionally calls the Google Maps Directions API if configured.
   - **`cost_matrix_loader.py`**  
     Constructs the cost (time) matrix from the depot and targets using the specified distance calculation method.
   - **`vrp_model_loader.py`**  
     Creates the OR-Tools Routing Model, adds time windows, optional visits (with penalty), and solves the VRP.
   - **`recalculation_assignment.py`**  
     Shows how to recalculate or update solutions, either from scratch or leveraging the previous solution.
   - **`test_main_with_mandatory_exact_time.py`**  
     A sample script demonstrating how to load JSON data, build the model, and solve a VRP with mandatory or exact-time targets.

---

## Technical Stack

- **Python 3.8+**  
- **OR-Tools** (Google Optimization Tools)  
- **Requests** (optional, for calling Google Maps API)  
- **Random / Math libraries** (for Haversine and mock data generation)  

All code is structured around Python modules, and can be run either as scripts or integrated into a larger system (e.g., wrapped by a Flask/FastAPI web service).

---

## Installation

```bash
# Create a Python virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# .\venv\Scripts\activate  # Windows

# Install requirements (make sure to include OR-Tools and other dependencies)
pip install -r requirements.txt

# If you plan to use Google Maps Directions:
# 1. Obtain a Google Maps API key
# 2. Add 'requests' to your requirements.txt or install it:
pip install requests
```

*Note:* You must also have OR-Tools installed. If it's not in `requirements.txt`, you can install it manually:
```bash
pip install ortools
```

---

## Usage

1. **Data Preparation**  
   - Make sure you have a **branch (depot) location** (latitude/longitude).
   - Prepare a list of **targets** (ID, lat/lon, stay time, mandatory flag, exact_time, etc.).
   - Define your **vehicles** (IDs, off-days if any).
   - Define your **date range** and **weekday time windows** (e.g., 8:00–19:00 on weekdays, none on weekends).

2. **Run the Sample Script**  
   - In `test_main_with_mandatory_exact_time.py`, you can see an example usage:
   - It loads `test_data.json`, constructs the model, and solves the VRP.
   - Adjust the JSON data to match your scenario (dates, times, mandatory flags).

3. **Generating the Cost Matrix**  
   - By default, `cost_matrix_loader.py` uses the Haversine distance with a random factor to simulate travel time.
   - If you have a valid Google Maps Directions API key, set:
     ```python
     use_google_api = True
     google_api_key = "YOUR_API_KEY"
     ```
     Then the code will attempt real driving time lookups.

4. **Viewing Results**  
   - After solving, you get a `solution` from OR-Tools. By iterating each vehicle route, you can extract:
     - The order of target visits
     - The arrival time
     - Which targets were skipped (due to penalty)
   - Customize your output format to produce the required schedule tables (e.g., day by day, person by person).

5. **Recalculation / Partial Updates**  
   - See `recalculation_assignment.py` for how you might take a previous solution, add or remove targets, and re-run the solver with a hint.

---

## Project Structure (Files & Folders)

- **`vrp_model_loader.py`**  
  Contains functions to build and configure the OR-Tools `RoutingModel`.
- **`recalculation_assignment.py`**  
  Demonstrates how to update an existing solution when new targets appear or conditions change.
- **`time_management.py`**  
  Parsing times, generating daily windows, handling weekends/holidays.
- **`distance_loader.py`**  
  Haversine distance or Google Maps Directions API calls.
- **`cost_matrix_loader.py`**  
  Creates the cost matrix (travel time) for the solver.
- **`data_provider.py`**  
  Loads data from CSV or JSON, returns branch info and target lists.
- **`branch_loader.py`** and **`targets_loader.py`**  
  Helpers for parsing CSV inputs.
- **`test_main_with_mandatory_exact_time.py`**  
  A basic main script demonstrating usage with mandatory and exact-time examples.
- **`test_data.json`**  
  Example JSON input showing how to define branch, targets, dates, vehicles, etc.

---

## Further Notes

- **Multiple-Day Scheduling**  
  This implementation treats each “day” for each “vehicle” as a unique virtual vehicle in OR-Tools. A route that spans multiple days effectively gets broken down so that each day starts and ends at the depot.  
- **Exact Time Windows**  
  Targets with an `exact_time` parameter get a time window like `(X, X)`, meaning the arrival must match precisely `X` minutes from the start of the day. This is a strict constraint; consider adjusting the time window to `(X, X+some_slack)` if you allow slight delays.
- **Performance**  
  For large numbers of targets (close to 100 with multi-day constraints), computation can become heavy. The default `timeout_seconds` is 10 seconds; OR-Tools will return the best feasible solution found within that window.
- **API Integration**  
  You may wrap these modules in a web API (FastAPI, Flask, etc.) or call them directly from a script. The modular design should facilitate easy integration.

---

**Please feel free to open issues or pull requests if you have questions or improvements.**  
