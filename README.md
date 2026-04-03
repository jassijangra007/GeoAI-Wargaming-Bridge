# Geospatial Decision-Support Architecture: Tactical Bridge Deployment & Off-Road Pathfinder

![Python](https://img.shields.io/badge/Python-3.x-blue.svg)
![ArcPy](https://img.shields.io/badge/ArcPy-Geospatial-green.svg)
![Status](https://img.shields.io/badge/Status-Simulation_Ready-brightgreen.svg)
![Version](https://img.shields.io/badge/Version-V35_Apex-red.svg)

## 📌 Architectural Overview

The **GeoAI Wargaming Bridge Pathfinder (V35 APEX)** is a deterministic, fully automated geospatial decision-support engine engineered via Python (ArcPy). Designed for complex wargaming simulations, this architecture identifies operationally viable pontoon bridge deployment sites across hydrographic barriers and charts highly camouflaged, off-road maneuver corridors for heavy armored vehicles.

This framework actively rejects static, point-based routing. Instead, it utilizes dynamic **Multi-Criteria Decision Analysis (MCDA)**, evaluating complex terrain limits, multi-hazard geoclimatic triggers (such as snowmelt surges and subsurface landslide risks), and tactical line-of-sight constraints to generate physically modeled 1D Vector Spans and stealth corridors.

---

## 🚀 Core Engine Capabilities

* **Dual-Bank Reconnaissance & Vector Fusion:** Eliminates the topological "hourglass pinch-point" (where traditional algorithms route entire armies into a single water pixel) by mathematically projecting 30m intelligence probes onto both riverbanks. It evaluates independent bank safety and generates physical Vector Polylines bridging the divide.
* **The Wilderness Override (Pure Off-Road Routing):** Bypasses algorithmic "Road Magnetism." The engine actively strips existing road infrastructure from the cost surface, forcing the pathfinder to calculate stealth corridors driven entirely by topographical safety and Sentinel-2 NDVI canopy camouflage.
* **Dynamic Hydro-Thermal Hazard Matrix:** Integrates a **Snowmelt Surge Protocol** and **Geotechnical Landslide Susceptibility Index (LSI)**. Fusing MODIS Land Surface Temperature with Snowpack and SoilGrids (Clay/Sand), the engine penalizes structural deployment in flash-flood zones or unstable slip-planes.
* **Triangulated Tactical Overwatch:** Automatically provisions mathematically separated (≥100m) surveillance towers strictly for Rank 1 and Rank 2 priority bridges based on precise Viewshed line-of-sight modeling.
* **POET Beachhead Jump:** Utilizes a *Point of Entry Tactical (POET)* maneuver, calculating precise overland routes to the exact Left and Right bank landing coordinates of the vector bridge, ensuring unbroken land-to-water topological continuity.

---

## 📂 Data Architecture & Input Requirements

The engine requires multi-modal, multi-resolution datasets to execute. To utilize this script, establish a local directory structure and populate it with the following dataset types. 

*Note: Update the input variables in the `Raw Data Inputs` section of the script to match your local repository paths.*

### 1. Topography & Spectral Intelligence
| Variable | Required Filename / Format | Geospatial Purpose |
| :--- | :--- | :--- |
| `DEM_PATH` | `P5_PAN_CD_N34_000_E076_000_DEM_30m.tif` | 30m USGS DEM. Derives Slope, Curvature, and base elevations for Viewshed analysis. |
| `S2_B04_RED` | `*_B04_10m.jp2` | Sentinel-2 L2A Red Band. Used dynamically to compute NDVI. |
| `S2_B08_NIR` | `*_B08_10m.jp2` | Sentinel-2 L2A Near-Infrared Band. Used dynamically to compute NDVI for stealth routing. |
| `LANDCOVER_TIF`| `IND_msk_cov.tif` | LULC map for supplementary terrain classification. |

### 2. Geoclimatic & Subsurface Hazards
| Variable | Required Filename / Format | Geospatial Purpose |
| :--- | :--- | :--- |
| `TEMP_TIF` | `MODIS_TEMP.tif` | MODIS Land Surface Temperature. Triggers the Thermal LSI multiplier and Snowmelt Surge. |
| `MODIS_SNOW` | `MODIS_Snow.tif` | Snow cover percentage. Combined with Temperature to predict hydrostatic flooding. |
| `CLAY_TIF` | `Clay_15-30cm.tif` | SoilGrids data. High clay percentages increase the Landslide Susceptibility Index (slip-plane risk). |
| `SAND_TIF` | `Sand_15-30cm.tif` | SoilGrids data. High sand mitigates landslide risk via drainage. |
| `MERIT_TIF` | `MERIT_ALL_BANDS_FIXED.tif` | MERIT Hydro data. Extracts upstream flow to avoid high-shear river bends. |

### 3. Tactical Vector Infrastructure
| Variable | Required Filename / Format | Geospatial Purpose |
| :--- | :--- | :--- |
| `RIVER_SHP` | `IND_water_lines_dcw.shp` | High-fidelity river centerlines (Diva GIS) used for Candidate Generation. |
| `ROADS_SHP` | `IND_roads.shp` | Logistics network. Used to calculate secondary access proximity for landing zones. |
| `GRWL_WIDTH_SHP`| `width_ni43.shp` | Global River Width from Landsat. Determines the exact required span length of the pontoon. |
| `BUILDINGS_SHP` | `Buildings.shp` | Urban footprint data to enforce chokepoint/building avoidance. |
| `ADMIN_SHP` | `IND_adm3.shp` | Administrative boundaries for spatial joining and filtering. |

### 4. Operational Nodes (User Defined)
| Variable | Required Filename / Format | Geospatial Purpose |
| :--- | :--- | :--- |
| `START_SHP` | `Start.shp` | The initial deployment node (Headquarters/Raw Material Depot). |
| `TARGET_SHP` | `Target.shp` | The final operational objective. |
| `ENEMY_OBSERVERS` | `Enemy_HighGround_Points.shp`| Hostile line-of-sight origins for generating Danger penalties. |
| `FRIENDLY_OBSERVERS`| `Our.shp` | Allied line-of-sight origins for generating Cover bonuses. |

---

## ⚙️ Modular Pipeline Execution

The `V35_APEX` engine executes autonomously through the following sequential modules:

1.  **Module 0 & 1 (Theater Extraction):** Crops all vector/raster data to the exact DEM boundary and processes fundamental Map Algebra (Slope, Curvature, NDVI).
2.  **Module 2 (Dual-Bank Recon):** Steps along the `RIVER_SHP` at 100m intervals, calculating geometric tangents to deploy intelligence probes exactly 30m inland on both banks.
3.  **Module 3 (CHIRPS Climatology):** Automatically scrapes global CHIRPS servers for 30 days of historical rainfall, stacking them into an accumulation model.
4.  **Module 3.5 (LSI Map Algebra):** Fuses Slope, Rain, Thermal, and Soil attributes into a localized Landslide Hazard Heatmap.
5.  **Module 4 (Spatial Intel Extraction):** Executes Viewshed analyses and multi-value point extraction to append environmental data to every candidate landing zone.
6.  **Module 5 (Decision Engine & Vector Fusion):** Ranks candidate pairs using the tactical weight matrix. Synthesizes the Top 10 sites into physical `POLYLINE` vectors, enforcing a 5km spatial separation limit.
7.  **Module 6 (Triangulated Overwatch):** Extracts the top topography surrounding Rank 1 and Rank 2 bridges, generating exactly three 100m-separated sniper/surveillance towers per site.
8.  **Module 7 (Off-Road Pathfinder):** Calculates massive-scale Cost Distance matrices, routing the `START_SHP` and `TARGET_SHP` to the specific Vector Bridge nodes. Generates the final **Detour Index** intelligence report.

---

## 📊 System Outputs

The engine creates a sterile execution environment inside the defined `OUTPUT_DIR` (default: `C:\Wargaming_Outputs`). 

**Generated Geodatabases & Intelligence:**
* `06_Priority_Vector_Bridges_[RUN_ID].gdb`: Contains isolated feature classes for the Top 10 tactical bridge spans.
* `08_Final_Assault_Routes_[RUN_ID].gdb`: Contains the final merged overland stealth routes and bridge vectors.
* `07_Tactical_Overwatch_Towers_[RUN_ID].shp`: Physical deployment coordinates for surveillance assets.
* **Terminal Output:** A printed Tactical Convoy Intelligence Report detailing the **Detour Index** (Actual Distance vs. Straight-Line Displacement) for every generated route.

---

## 💻 System Requirements & Usage

**Prerequisites:**
* **ArcGIS Pro:** Advanced License with **Spatial Analyst** Extension enabled.
* **Python 3.x:** Configured strictly within the `arcpy` conda environment.
* **Internet Access:** Required during runtime for Module 3 (CHIRPS automated fetching).

**Execution:**
1.  Clone this repository.
2.  Organize your raw datasets matching the filenames specified in the Data Architecture section.
3.  Update the `DEM_PATH`, `S2_B04_RED`, `S2_B08_NIR`, and base directory paths inside the script to point to your localized data vault.
4.  Execute via Python Command Prompt:
    ```bash
    python Wargaming_Pathfinder_V35.py
    ```

---

## 👤 Author

**Jassi**
* GitHub: [jassijangra007](https://github.com/jassijangra007)

*Disclaimer: This repository is intended strictly for academic research, spatial optimization theory, and civilian wargaming simulation methodologies.*
