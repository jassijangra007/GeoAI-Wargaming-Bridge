# Geospatial Decision-Support Architecture: Tactical Bridge Deployment & Off-Road Pathfinder
---
**View 3D WebGL Simulation here:**
[ https://jassijangra007.github.io/GeoAI-Wargaming-Bridge/ ]
---
![Python](https://img.shields.io/badge/Python-3.x-blue.svg)
![ArcPy](https://img.shields.io/badge/ArcPy-Geospatial-green.svg)
![Status](https://img.shields.io/badge/Status-Simulation_Ready-brightgreen.svg)
![Version](https://img.shields.io/badge/Version-V35_Apex-red.svg)
![License](https://img.shields.io/badge/License-MIT-purple.svg)

## 📌 Executive Summary

The **GeoAI Wargaming Bridge Pathfinder (V35 APEX)** is a fully automated, deterministic spatial decision-support engine engineered via Python (ArcPy). Designed specifically for high-stakes wargaming simulations in the extreme topography of the Kargil Sector (Indus River), this architecture solves one of military logistics' most complex problems: identifying structurally viable, tactically secure pontoon bridge deployment sites and charting highly camouflaged off-road maneuver corridors for heavy armored vehicles.

This framework actively rejects static, point-based GIS suitability modeling. Instead, it utilizes dynamic **Multi-Criteria Decision Analysis (MCDA)**, evaluating strict topographical limits, multi-hazard geoclimatic triggers (such as snowmelt surges and subsurface landslide risks), and tactical line-of-sight constraints to generate physically modeled 1D Vector Spans.

---

## 🚀 Core Architectural Innovations

Standard routing algorithms (like Dijkstra's or Least-Cost Path) fail in tactical wargaming due to "Road Magnetism" and topological errors. This engine introduces custom spatial logic to neutralize those flaws:

* **Dual-Bank Reconnaissance & Vector Fusion:** Standard routing algorithms route entire armies into a single "hourglass pinch-point" on the water. This engine eliminates that flaw by mathematically stepping along the river centerline at 100m intervals, calculating geometric tangents, and projecting 30m intelligence probes onto *both* riverbanks. It independently evaluates Left and Right bank safety before generating a physical Vector Polyline bridging the divide.
* **The Wilderness Override (Pure Off-Road Routing):** Standard cost-surface algorithms heavily favor existing roads. This engine actively strips `IND_roads.shp` from the base friction matrix. It forces the pathfinder to calculate stealth corridors driven entirely by topographical safety (<15% slope) and canopy camouflage derived from Sentinel-2 NDVI processing.
* **POET Beachhead Pathfinder:** Utilizes a *Point of Entry Tactical (POET)* maneuver. The algorithm calculates precise overland least-cost paths to the exact Left and Right bank landing coordinates of the vector bridge, ensuring unbroken land-to-water topological continuity without routing failures.
* **Triangulated Tactical Overwatch:** Automatically provisions mathematically separated (≥100m) surveillance towers strictly for Rank 1 and Rank 2 priority bridges based on precise Viewshed line-of-sight modeling using the 30m DEM.
* **Dynamic Hydro-Thermal Hazard Matrix:** Integrates a **Snowmelt Surge Protocol** and **Geotechnical Landslide Susceptibility Index (LSI)**. Fusing MODIS Land Surface Temperature with Snowpack and SoilGrids (Clay/Sand), the engine penalizes structural deployment in flash-flood zones or unstable slip-planes.

---

## 📂 Detailed Data Dictionary & Input Architecture

The engine requires the harmonization of multi-modal, multi-resolution datasets. *Note: Due to GitHub size limits, raw datasets (TIFs, large shapefiles) are not hosted in this repository. Ensure your local environment matches the directory paths defined in the script.*

### 1. Topography & Spectral Intelligence
| Dataset Variable | Target Filename | Geospatial Purpose & Algorithm Role |
| :--- | :--- | :--- |
| `DEM_PATH` | `P5_PAN_CD_N34_000_E076_000_DEM_30m.tif` | 30m USGS DEM. Foundational layer driving Slope extraction (<15% vehicle limit), Curvature mapping, and Enemy/Friendly Viewshed analysis. |
| `S2_B04_RED` | `*_B04_10m.jp2` | Sentinel-2 L2A Red Band. Used dynamically by the Map Algebra engine to compute NDVI. |
| `S2_B08_NIR` | `*_B08_10m.jp2` | Sentinel-2 L2A Near-Infrared Band. High NDVI areas (>0.4) are rewarded as "Stealth Corridors" in the Wilderness Override. |
| `LANDCOVER_TIF`| `IND_msk_cov.tif` | LULC map for supplementary terrain classification and friction calculation. |

### 2. Geoclimatic & Subsurface Hazards
| Dataset Variable | Target Filename | Geospatial Purpose & Algorithm Role |
| :--- | :--- | :--- |
| `TEMP_TIF` | `MODIS_TEMP.tif` | MODIS Land Surface Temperature. Triggers the Thermal LSI multiplier and activates the Snowmelt Surge Protocol if >10% snow is present. |
| `MODIS_SNOW` | `MODIS_Snow.tif` | MODIS Snow cover percentage. Combined with Temperature to predict hydrostatic flash floods. |
| `CLAY_TIF` | `Clay_15-30cm.tif` | SoilGrids data (15-30cm depth). High clay percentages retain moisture, acting as a slip-plane and increasing the Landslide Susceptibility Index. |
| `SAND_TIF` | `Sand_15-30cm.tif` | SoilGrids data. High sand mitigates landslide risk via rapid drainage, increasing bank stability. |
| `MERIT_TIF` | `MERIT_ALL_BANDS_FIXED.tif` | MERIT Hydro data. Extracts upstream flow speeds. Used to explicitly avoid high-shear, high-erosion river bends. |

### 3. Tactical Vector Infrastructure
| Dataset Variable | Target Filename | Geospatial Purpose & Algorithm Role |
| :--- | :--- | :--- |
| `RIVER_SHP` | `IND_water_lines_dcw.shp` | High-fidelity river centerlines (Diva GIS). Serves as the geometric baseline for candidate generation. |
| `ROADS_SHP` | `IND_roads.shp` | Logistics network. Used strictly to calculate secondary access proximity for landing zones post-crossing. |
| `GRWL_WIDTH_SHP`| `width_ni43.shp` | Global River Width from Landsat. Determines the exact required span length of the pontoon bridging equipment. |
| `BUILDINGS_SHP` | `Buildings.shp` | Urban footprint data utilized to enforce urban chokepoint avoidance during routing. |

### 4. Operational Nodes (User Defined Constraints)
| Dataset Variable | Target Filename | Geospatial Purpose & Algorithm Role |
| :--- | :--- | :--- |
| `START_SHP` | `Start.shp` | The initial deployment node (e.g., Logistical Headquarters or Raw Material Depot). |
| `TARGET_SHP` | `Target.shp` | The final operational objective on the opposite side of the hydrographic barrier. |
| `ENEMY_OBSERVERS` | `Enemy_HighGround_Points.shp`| Hostile line-of-sight origins. Points visible to these nodes incur massive tactical penalties. |
| `FRIENDLY_OBSERVERS`| `Our.shp` | Allied line-of-sight origins for generating Cover bonuses and protecting the crossing. |

---
## **You May Find All RAW INPUT files here**- https://mega.nz/file/KgwkCRgS#Yg72SzuKUsmdZaBTtI2DP4G7LR9vM8nOtZILv7XBSjQ

---
## ⚙️ Module-by-Module Execution Flow

The `V35_APEX` engine executes autonomously through 7 sequential processing modules.

### **Module 1: Theater Extraction & Spectral Preprocessing**
The script initializes by enforcing a rigid `UTM Zone 43N` coordinate system to ensure all planar distance calculations are metrically perfect. It clips all vector geometries to the extent of the USGS DEM and utilizes ArcPy Spatial Analyst (Map Algebra) to derive Slope, Curvature, and compute the Sentinel-2 NDVI raster.

### **Module 2: Dual-Bank Candidate Generation**
The algorithm iterates along the `RIVER_SHP` geometry. At every 100-meter interval, it calculates the mathematical tangent angle of the river's flow, rotates exactly 90 degrees, and projects `arcpy.Point` geometries 30 meters inland onto the Left and Right banks. This generates thousands of paired "intelligence probes."

### **Module 3: Automated CHIRPS Climatology Scraper**
The script bypasses static weather data by initiating a `urllib` scraper targeting the UCSB CHIRPS database. It fetches 30 days of historical daily rainfall data and utilizes `CellStatistics` to stack and sum the data into a localized 30-Day Precipitation Accumulation model.

### **Module 3.5: Geotechnical LSI Map Algebra**
Generates the Landslide Susceptibility Index (LSI). The script normalizes SoilGrids Clay and Sand fractions, fusing them with the 30-Day Rainfall model and Topographical Slope. A secondary thermal multiplier (MODIS LST) is applied to account for heat-induced soil degradation.

### **Module 4: Full Spatial Intelligence Extraction**
Executes heavy `Viewshed` processing for Enemy and Friendly observers. It runs `GenerateNearTable` to calculate logistical proximity to the `ROADS_SHP`. Finally, it utilizes `ExtractMultiValuesToPoints` to stamp every single Left and Right bank probe with exact values for Slope, Flow Speed, NDVI, Rainfall, LSI, and Exposure.

### **Module 5: Decision Engine & Vector Bridge Fusion**
The core MCDA logic. The engine scores each bank independently. If a Left Bank is perfectly safe but the Right Bank is a sheer cliff (>15% slope), the bridge fails. For passing pairs, the script physically draws an `arcpy.Polyline` spanning the river, calculating the bridging cost. The Top 10 sites are isolated and saved into a Geodatabase, enforcing a strict 5km minimum separation distance to guarantee operational diversity.

### **Module 6: Triangulated Overwatch Provisioning**
Securing the crossing. The engine isolates the Rank 1 and Rank 2 priority bridges, runs localized Viewsheds, and extracts an array of the highest surrounding elevations. It enforces a spatial loop to select exactly three peaks per bridge that are strictly separated by at least 100 meters, ensuring sniper/surveillance units do not cluster redundantly.

### **Module 7: Pure Off-Road Pathfinder & Detour Calculator**
The POET Beachhead execution. The engine calculates massive `CostDistance` and `CostBackLink` rasters from the `START_SHP` and `TARGET_SHP` using a friction surface driven entirely by Slope and NDVI. It routes the start node to the left bank, and the target node to the right bank, merging them with the Vector Bridge.

---

## 🧮 Mathematical Framework & Validation Metrics

The engine evaluates routes based on rigorous mathematical constraints. The most critical output metric is the **Detour Index**, which prevents the AI from generating overly convoluted stealth corridors that exhaust supply lines.

`Detour Index = Actual Generated Overland Path (km) / Straight-Line Geometric Displacement (km)`

* **Optimal Route:** Detour Index < 1.25
* **Moderate Route:** Detour Index 1.25 - 1.49
* **Flagged / Severe Detour:** Detour Index ≥ 1.50 (Requires Commander Review)

---

## 📊 System Outputs & Deliverables

The engine operates safely within a scratch workspace before committing final geometries to `C:\Wargaming_Outputs\`. 

**Final Exported Geodatabases:**
* `06_Priority_Vector_Bridges_[RUN_ID].gdb`: Contains isolated, physically modeled Top 10 Vector Bridge spans.
* `08_Final_Assault_Routes_[RUN_ID].gdb`: Contains the fully merged overland stealth maneuver corridors.
* `07_Tactical_Overwatch_Towers_[RUN_ID].shp`: Triangulated surveillance points for forward deployment.
* **Terminal Output:** A detailed, printed *Tactical Convoy Intelligence Report* evaluating the exact length, displacement, and Detour Index of every generated route.

---

## 💻 Installation & Usage Instructions

**Prerequisites:**
* **ArcGIS Pro** (Advanced License Recommended).
* **ArcGIS Spatial Analyst Extension** (Must be checked out/enabled).
* **Python 3.x** (Must be configured with the standard `arcpy` conda environment).
* **Internet Access:** Required during runtime for Module 3 (CHIRPS fetching).

**Execution Steps:**
1.  **Clone the Repository:**
    ```bash
    git clone [https://github.com/jassijangra007/GeoAI-Wargaming-Bridge.git](https://github.com/jassijangra007/GeoAI-Wargaming-Bridge.git)
    cd GeoAI-Wargaming-Bridge
    ```
2.  **Prepare the Workspace:**
    * Create a local directory, e.g., `C:\FOSS_Tools\`.
    * Place all required raster and shapefile inputs (listed in the Data Dictionary above) into this directory.
    * Ensure your `Start.shp` and `Target.shp` are properly defined for your specific Area of Interest.
3.  **Run the Engine:**
    * Open your ArcGIS Pro Python Command Prompt or your IDE.
    * Execute the script:
    ```bash
    python Wargaming_Pathfinder_V35.py
    ```

---

## 👤 Author

**Jassi**

---
*Disclaimer: This repository is intended strictly for academic research, spatial optimization theory, and civilian wargaming simulation methodologies. The geoclimatic algorithms presented herein are generalized for simulation and require further calibration for real-world disaster management or structural engineering deployment.*
