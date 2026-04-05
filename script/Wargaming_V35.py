# ==============================================================================
# 🚀 GEOSPATIAL DECISION ENGINE: WARGAMING BRIDGE DEPLOYMENT (V35 APEX FINAL)
# ==============================================================================
# Description: Ultimate operational pathfinder and Multi-Hazard Tactical Scorer.
# Upgrades in this version:
#   - STATS FIX: Resolves ERROR 001100 by calculating raster statistics natively.
#   - TACTICAL OVERWATCH: RANK_01 and RANK_02 now get exactly 3 triangulated 
#     surveillance towers each (separated by 100m).
#   - THERMAL INTEGRATION: MODIS Temperature added as a secondary multiplier. 
#   - GEOTECHNICAL LSI: Integrates Sand and Clay subsurface textures with Slope.
#   - DUAL-BANK RECON: Evaluates both sides of the river, spanning them with Vectors.
#   - PURE OFF-ROAD: Terrain Slope + NDVI dictate the path (Roads Ignored).
# ==============================================================================

import arcpy
import os
import sys
import datetime
import math
import urllib.request
import gzip
import shutil
from datetime import date, timedelta
from arcpy.sa import *

# ==============================================================================
# 🟢 SYSTEM & WORKSPACE SETTINGS
# ==============================================================================
DEBUG_MODE = True
arcpy.env.overwriteOutput = True
arcpy.env.addOutputsToMap = False
# Force all output to UTM Zone 43N for accurate metric distance calculations
arcpy.env.outputCoordinateSystem = arcpy.SpatialReference(32643)

RUN_ID = datetime.datetime.now().strftime("%H%M%S")
OUTPUT_DIR = r"C:\Wargaming_Outputs"
RAINFALL_DIR = r"C:\FOSS_Tools\Rainfall"

# Create necessary directories if they do not exist
for directory in [OUTPUT_DIR, RAINFALL_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)

# Setup a local Geodatabase cache to handle intermediate vector/raster processing safely
SCRATCH_GDB = os.path.join(OUTPUT_DIR, "Wargaming_Processing_Cache.gdb")
if not arcpy.Exists(SCRATCH_GDB):
    arcpy.management.CreateFileGDB(OUTPUT_DIR, "Wargaming_Processing_Cache.gdb")

arcpy.env.workspace = SCRATCH_GDB
arcpy.env.scratchWorkspace = OUTPUT_DIR

# ==============================================================================
# 🟢 RAW DATA INPUTS
# ==============================================================================
# Base Topography and Satellite Imagery
DEM_PATH      = r"C:\FOSS_Tools\USGS\P5_PAN_CD_N34_000_E076_000_30m\P5_PAN_CD_N34_000_E076_000_DEM_30m.tif"
S2_B04_RED    = r"C:\FOSS_Tools\USGS\S2C_MSIL2A_20250620T053701_N0511_R005_T43SFU_20250620T093416.SAFE\GRANULE\L2A_T43SFU_A004122_20250620T054238\IMG_DATA\R10m\T43SFU_20250620T053701_B04_10m.jp2"
S2_B08_NIR    = r"C:\FOSS_Tools\USGS\S2C_MSIL2A_20250620T053701_N0511_R005_T43SFU_20250620T093416.SAFE\GRANULE\L2A_T43SFU_A004122_20250620T054238\IMG_DATA\R10m\T43SFU_20250620T053701_B08_10m.jp2"

# Hydrology, Climatology, Soils, and Hazards
MERIT_TIF     = r"C:\FOSS_Tools\MERIT_ALL_BANDS_FIXED.tif"
MODIS_SNOW    = r"C:\FOSS_Tools\MODIS_Snow.tif" 
TEMP_TIF      = r"C:\FOSS_Tools\MODIS_TEMP.tif"    
CLAY_TIF      = r"C:\FOSS_Tools\Clay_15-30cm.tif"  
SAND_TIF      = r"C:\FOSS_Tools\Sand_15-30cm.tif"  

# Vector Ground Truth Layers
RIVER_SHP          = r"C:\FOSS_Tools\IND_water_lines_dcw.shp"             
ROADS_SHP          = r"C:\FOSS_Tools\IND_roads.shp"    
ADMIN_SHP          = r"C:\FOSS_Tools\IND_adm3.shp"         
LANDCOVER_TIF      = r"C:\FOSS_Tools\IND_msk_cov.tif"      
ENEMY_OBSERVERS    = r"C:\FOSS_Tools\Enemy_HighGround_Points.shp" 
FRIENDLY_OBSERVERS = r"C:\FOSS_Tools\Our.shp" 
GRWL_WIDTH_SHP     = r"C:\FOSS_Tools\width_ni43.shp"
BUILDINGS_SHP      = r"C:\FOSS_Tools\Buildings.shp"

# Logistics Points
START_SHP          = r"C:\FOSS_Tools\Start.shp"
TARGET_SHP         = r"C:\FOSS_Tools\Target.shp"

# ==============================================================================
# 🟢 TACTICAL CONSTRAINTS & WEIGHTS
# ==============================================================================
# CHIRPS settings for fetching historical rain data
RAIN_START_DATE = date(2025, 6, 15)
RAIN_END_DATE   = date(2025, 7, 15)
CHIRPS_BASE_URL = "https://data.chc.ucsb.edu/products/CHIRPS-2.0/global_daily/tifs/p25/"

# Hazard Matrix Weights (Flood)
W_FLOOD_RAIN, W_FLOOD_ELEV, W_FLOOD_NDVI, W_FLOOD_SLOPE = 0.40, 0.25, 0.20, 0.15

# Physical Limitations
MAX_SLOPE_PERCENT    = 15.0  
BRIDGE_INTERVAL      = 100   
ROAD_BUFFER_METERS   = 3000  
TARGET_BRIDGE_COUNT  = 10    
MIN_SEPARATION_METERS = 5000 
TOWER_BUFFER_METERS  = 1000  
MAX_DETOUR_INDEX     = 1.5   
BANK_BUFFER_DIST     = 30    

# Tactical Bridge Scoring Weights (Must sum to 1.0)
W_CONCEALMENT, W_LOGISTICS, W_SAFETY = 0.30, 0.20, 0.50 

arcpy.CheckOutExtension("Spatial")

def log_debug(message):
    """Custom logging function to print verbose status updates."""
    if DEBUG_MODE:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] 💡 DEBUG: {message}")

def validate_inputs():
    print("\n" + "="*50)
    print("🔍 PRE-FLIGHT DATA INTEGRITY CHECK")
    print("="*50)
    
    all_ok = True
    critical_files = [
        (DEM_PATH, "Elevation DEM"), (S2_B04_RED, "Sentinel Red Band"), (S2_B08_NIR, "Sentinel NIR Band"), 
        (CLAY_TIF, "Clay Soil Map"), (SAND_TIF, "Sand Soil Map"),
        (RIVER_SHP, "River Vectors"), (ROADS_SHP, "Road Vectors"), (START_SHP, "Convoy Start"), (TARGET_SHP, "Convoy Target")
    ]
    for layer, name in critical_files:
        if arcpy.Exists(layer): 
            print(f"  ✅ [AVAILABLE] {name}")
        else:
            print(f"  ❌ [MISSING]   {name} -> {layer}")
            all_ok = False
            
    optional_files = [
        (MERIT_TIF, "MERIT Hydro Flow"), (TEMP_TIF, "MODIS Temperature"), 
        (GRWL_WIDTH_SHP, "GRWL River Widths"), (BUILDINGS_SHP, "Urban Buildings"), 
        (MODIS_SNOW, "MODIS Snowmelt Data"), (ENEMY_OBSERVERS, "Enemy Intel"), 
        (FRIENDLY_OBSERVERS, "Friendly Intel")
    ]
    
    print("\n--- OPTIONAL FILES ---")
    for layer, name in optional_files:
        if arcpy.Exists(layer): print(f"  ✅ [AVAILABLE] {name}")
        else: print(f"  ⚠️ [WARNING]   {name} -> Not Found. Engine will adapt.")
            
    print("="*50 + "\n")
    return all_ok

def safe_delete(fc_path):
    if arcpy.Exists(fc_path):
        try: arcpy.management.Delete(fc_path)
        except Exception: pass

# ------------------------------------------------------------------------------
# ✂️ MODULE 0 & 1: THEATER, TERRAIN, AND NDVI CAMOUFLAGE
# ------------------------------------------------------------------------------
def extract_theater_and_terrain(out_folder):
    log_debug("Module 0 & 1: Generating Area of Interest (AOI), Terrain Maps, and Camouflage Layers...")
    
    dem_desc = arcpy.Describe(DEM_PATH)
    
    log_debug(" -> Clipping River and Road vectors to match Theater extent...")
    aoi_poly = os.path.join(SCRATCH_GDB, f"AOI_Boundary_{RUN_ID}")
    arcpy.management.CopyFeatures([arcpy.Polygon(arcpy.Array([dem_desc.extent.lowerLeft, dem_desc.extent.lowerRight, dem_desc.extent.upperRight, dem_desc.extent.upperLeft, dem_desc.extent.lowerLeft]), dem_desc.spatialReference)], aoi_poly)
    
    loc_riv = os.path.join(SCRATCH_GDB, f"Clipped_Rivers_{RUN_ID}")
    arcpy.analysis.Clip(RIVER_SHP, aoi_poly, loc_riv)
    
    loc_rd = os.path.join(SCRATCH_GDB, f"Clipped_Roads_{RUN_ID}")
    arcpy.analysis.Clip(ROADS_SHP, aoi_poly, loc_rd)
    
    loc_bldg = None
    if arcpy.Exists(BUILDINGS_SHP):
        loc_bldg = os.path.join(SCRATCH_GDB, f"Clipped_Buildings_{RUN_ID}")
        arcpy.analysis.Clip(BUILDINGS_SHP, aoi_poly, loc_bldg)
    
    log_debug(" -> Executing Map Algebra for Slope & Curvature...")
    slope_rast = os.path.join(out_folder, f"01a_Terrain_Slope_Map_{RUN_ID}.tif")
    Slope(DEM_PATH, "PERCENT_RISE").save(slope_rast)
    
    curv_rast = os.path.join(out_folder, f"01b_Terrain_Curvature_Map_{RUN_ID}.tif")
    Curvature(DEM_PATH).save(curv_rast)

    log_debug(" -> Rendering NDVI Raster (Vegetation Index) for Tactical Off-Road routing...")
    red, nir = Raster(S2_B04_RED), Raster(S2_B08_NIR)
    ndvi_rast = os.path.join(out_folder, f"02_Camouflage_NDVI_Map_{RUN_ID}.tif")
    ((nir - red) / (nir + red + 0.001)).save(ndvi_rast)
    
    return loc_riv, loc_rd, loc_bldg, slope_rast, curv_rast, ndvi_rast

# ------------------------------------------------------------------------------
# 🎯 MODULE 2: DUAL-BANK CANDIDATE GENERATION
# ------------------------------------------------------------------------------
def generate_dual_bank_candidates(loc_riv):
    log_debug("Module 2: Executing Dual-Bank Reconnaissance (Left & Right Bank Evaluation)...")
    out_pts = os.path.join(SCRATCH_GDB, f"DualBank_Candidates_{RUN_ID}")
    
    sr = arcpy.Describe(loc_riv).spatialReference
    arcpy.management.CreateFeatureclass(SCRATCH_GDB, f"DualBank_Candidates_{RUN_ID}", "POINT", spatial_reference=sr)
    arcpy.management.AddField(out_pts, "Bank_Side", "TEXT")
    arcpy.management.AddField(out_pts, "Pair_ID", "LONG")

    pts_created = 0
    pair_id = 1
    
    with arcpy.da.SearchCursor(loc_riv, ["SHAPE@"]) as s_cur:
        with arcpy.da.InsertCursor(out_pts, ["SHAPE@", "Bank_Side", "Pair_ID"]) as i_cur:
            for row in s_cur:
                geom = row[0]
                if not geom: continue
                d = 0.0
                while d <= geom.length:
                    center_pt = geom.positionAlongLine(d, False).firstPoint
                    p1 = geom.positionAlongLine(max(0, d - 1), False).firstPoint
                    p2 = geom.positionAlongLine(min(geom.length, d + 1), False).firstPoint
                    angle = math.atan2(p2.Y - p1.Y, p2.X - p1.X)
                    
                    angle_left = angle + (math.pi / 2)
                    angle_right = angle - (math.pi / 2)
                    
                    left_x = center_pt.X + (math.cos(angle_left) * BANK_BUFFER_DIST)
                    left_y = center_pt.Y + (math.sin(angle_left) * BANK_BUFFER_DIST)
                    right_x = center_pt.X + (math.cos(angle_right) * BANK_BUFFER_DIST)
                    right_y = center_pt.Y + (math.sin(angle_right) * BANK_BUFFER_DIST)
                    
                    i_cur.insertRow([arcpy.PointGeometry(arcpy.Point(left_x, left_y), sr), "LEFT", pair_id])
                    i_cur.insertRow([arcpy.PointGeometry(arcpy.Point(right_x, right_y), sr), "RIGHT", pair_id])
                    
                    d += BRIDGE_INTERVAL
                    pair_id += 1
                    pts_created += 2
                    
    log_debug(f" -> Deployed {pts_created} intelligence probes across both river banks.")
    return out_pts

# ------------------------------------------------------------------------------
# 🌧️ MODULE 3: AUTOMATED CHIRPS RAINFALL PIPELINE
# ------------------------------------------------------------------------------
def process_climatology(start_date, end_date, out_folder):
    log_debug("Module 3: Booting up Automated CHIRPS Climatology Scraper...")
    delta = end_date - start_date
    daily_rasters = []

    log_debug(f" -> Checking remote archive for rainfall data between {start_date} and {end_date}...")
    for i in range(delta.days + 1):
        current_date = start_date + timedelta(days=i)
        year_str = current_date.strftime("%Y")
        month_str = current_date.strftime("%m")
        day_str = current_date.strftime("%d")
        
        file_name = f"chirps-v2.0.{year_str}.{month_str}.{day_str}.tif"
        gz_name = file_name + ".gz"
        url = f"{CHIRPS_BASE_URL}{year_str}/{gz_name}"
        gz_path = os.path.join(RAINFALL_DIR, gz_name)
        tif_path = os.path.join(RAINFALL_DIR, file_name)
        
        if not os.path.exists(tif_path) or arcpy.env.overwriteOutput:
            try:
                urllib.request.urlretrieve(url, gz_path)
                with gzip.open(gz_path, 'rb') as f_in:
                    with open(tif_path, 'wb') as f_out: shutil.copyfileobj(f_in, f_out)
                os.remove(gz_path) 
            except Exception:
                continue 
        daily_rasters.append(tif_path)

    if not daily_rasters: 
        log_debug("  ⚠️ No historical rainfall data fetched. Rain math bypassed.")
        return None

    log_debug(" -> Stacking daily rasters into a 30-Day Accumulation Model...")
    total_rain = CellStatistics(daily_rasters, "SUM", "DATA")
    rain_out_path = os.path.join(out_folder, f"03a_Climatology_30Day_Rainfall_{RUN_ID}.tif")
    total_rain.save(rain_out_path)
    return rain_out_path

# ------------------------------------------------------------------------------
# 🌋 MODULE 3.5: GEOTECHNICAL SOIL & THERMAL LANDSLIDE (LSI) MAP ALGEBRA
# ------------------------------------------------------------------------------
def generate_landslide_hazard_map(slope_rast, rain_rast, clay_tif, sand_tif, temp_tif, out_folder):
    log_debug("Module 3.5: Executing Map Algebra for Thermal/Geotechnical Landslide Model...")
    
    log_debug(" -> Analyzing Subsurface Textures (Clay/Sand ratios)...")
    clay_norm = Raster(clay_tif) / 100.0
    sand_norm = Raster(sand_tif) / 100.0
    
    # Soil Risk (High Clay = High Risk. High Sand = Low Risk)
    soil_risk = (clay_norm * 0.7) + ((1.0 - sand_norm) * 0.3)
    
    log_debug(" -> Normalizing Topography against 45-degree slip limits...")
    slope_norm = Raster(slope_rast) / 45.0
    slope_norm = Con(slope_norm > 1.0, 1.0, slope_norm)
    
    if rain_rast and arcpy.Exists(rain_rast):
        # 🔥 FIX 001100: Calculate statistics before getting max value
        arcpy.management.CalculateStatistics(rain_rast)
        rain_max = float(arcpy.management.GetRasterProperties(rain_rast, "MAXIMUM").getOutput(0))
        rain_norm = Raster(rain_rast) / rain_max if rain_max > 0 else 0.0
    else:
        rain_norm = 0.0

    # Base Landslide Soil Risk Fusion
    lsi_risk = (slope_norm * 0.5) + (rain_norm * 0.3) + (soil_risk * 0.2)

    if temp_tif and arcpy.Exists(temp_tif):
        log_debug(" -> Applying Secondary Thermal Multiplier to Landslide Risk...")
        # 🔥 FIX 001100: Calculate statistics before getting min/max
        arcpy.management.CalculateStatistics(temp_tif)
        t_min = float(arcpy.management.GetRasterProperties(temp_tif, "MINIMUM").getOutput(0))
        t_max = float(arcpy.management.GetRasterProperties(temp_tif, "MAXIMUM").getOutput(0))
        if t_max > t_min:
            temp_norm = (Raster(temp_tif) - t_min) / (t_max - t_min)
            lsi_risk = lsi_risk + (temp_norm * 0.10) 
    
    lsi_path = os.path.join(out_folder, f"03b_Landslide_Thermal_Risk_Heatmap_{RUN_ID}.tif")
    lsi_risk.save(lsi_path)
    
    log_debug(f"✅ Landslide Heatmap Generated: {lsi_path}")
    return lsi_path

# ------------------------------------------------------------------------------
# 👁️ MODULE 4: FULL SPATIAL INTELLIGENCE EXTRACTION
# ------------------------------------------------------------------------------
def extract_spatial_intel(points_fc, dem_path, slope_path, curv_path, merit_tif, temp_path, rain_path, snow_path, lsi_path, local_bldgs, red_band, nir_band, out_folder):
    log_debug("Module 4: Spatial Intel Extraction (Thermal, Line of Sight, Logistics)...")

    sj_admin = os.path.join(SCRATCH_GDB, f"SJ_AdminData_{RUN_ID}")
    if arcpy.Exists(ADMIN_SHP):
        arcpy.analysis.SpatialJoin(points_fc, ADMIN_SHP, sj_admin, "JOIN_ONE_TO_ONE", "KEEP_ALL", match_option="INTERSECT")
    else:
        arcpy.management.CopyFeatures(points_fc, sj_admin)

    sj_out_fc = os.path.join(SCRATCH_GDB, f"SJ_MasterData_{RUN_ID}")
    if arcpy.Exists(GRWL_WIDTH_SHP):
        arcpy.analysis.SpatialJoin(sj_admin, GRWL_WIDTH_SHP, sj_out_fc, "JOIN_ONE_TO_ONE", "KEEP_ALL", match_option="CLOSEST")
    else:
        arcpy.management.CopyFeatures(sj_admin, sj_out_fc)

    log_debug(" -> Executing Tactical Line-of-Sight Analysis (Viewshed)...")
    viewshed_enemy = os.path.join(out_folder, f"04a_Enemy_LineOfSight_Risk_{RUN_ID}.tif")
    if arcpy.Exists(ENEMY_OBSERVERS):
        try: 
            Viewshed(dem_path, ENEMY_OBSERVERS).save(viewshed_enemy)
            arcpy.management.BuildRasterAttributeTable(viewshed_enemy, "Overwrite")
            arcpy.management.AddField(viewshed_enemy, "Risk_Level", "TEXT", field_length=50)
            with arcpy.da.UpdateCursor(viewshed_enemy, ["Value", "Risk_Level"]) as cur:
                for row in cur:
                    row[1] = "SAFE (Hidden from Enemy)" if row[0] == 0 else f"DANGER (Seen by {row[0]} Enemy Observers)"
                    cur.updateRow(row)
        except Exception: 
            viewshed_enemy = None
    else: viewshed_enemy = None

    viewshed_friendly = os.path.join(out_folder, f"04b_Friendly_Overwatch_Coverage_{RUN_ID}.tif")
    if arcpy.Exists(FRIENDLY_OBSERVERS):
        try: 
            Viewshed(dem_path, FRIENDLY_OBSERVERS).save(viewshed_friendly)
            arcpy.management.BuildRasterAttributeTable(viewshed_friendly, "Overwrite")
            arcpy.management.AddField(viewshed_friendly, "CoverLevel", "TEXT", field_length=50)
            with arcpy.da.UpdateCursor(viewshed_friendly, ["Value", "CoverLevel"]) as cur:
                for row in cur:
                    row[1] = "BLIND (No Friendly Cover)" if row[0] == 0 else f"COVERED (Protected by {row[0]} Friendly Observers)"
                    cur.updateRow(row)
        except Exception: 
            viewshed_friendly = None
    else: viewshed_friendly = None

    log_debug(" -> Scanning Dual-Bank Road Access...")
    road_dist_dict, bldg_dist_dict = {}, {}
    near_scratch = os.path.join(SCRATCH_GDB, f"Near_Table_TempPoints_{RUN_ID}")
    
    try:
        arcpy.management.CopyFeatures(sj_out_fc, near_scratch)
        near_table = os.path.join(SCRATCH_GDB, f"Near_Table_RoadAccess_{RUN_ID}")
        arcpy.analysis.GenerateNearTable(near_scratch, ROADS_SHP, near_table, search_radius=f"{ROAD_BUFFER_METERS} Meters", location="NO_LOCATION", angle="ANGLE", closest="ALL", closest_count=10)
        
        road_access_data = {}
        with arcpy.da.SearchCursor(near_table, ["IN_FID", "NEAR_DIST", "NEAR_ANGLE"]) as cur:
            for row in cur:
                pt_id, dist, angle = row[0], row[1], row[2]
                if pt_id not in road_access_data: road_access_data[pt_id] = []
                road_access_data[pt_id].append((dist, angle))
                
        if local_bldgs and arcpy.Exists(local_bldgs):
            arcpy.analysis.Near(near_scratch, local_bldgs)
            with arcpy.da.SearchCursor(near_scratch, ["OID@", "NEAR_DIST"]) as cur:
                for row in cur: bldg_dist_dict[row[0]] = row[1]
    finally:
        safe_delete(near_scratch)
        safe_delete(near_table)

    dual_access_dict = {} 
    for pt_id, roads in road_access_data.items():
        if len(roads) < 2:
            dual_access_dict[pt_id] = (0, roads[0][0] if roads else 50000.0)
            continue

        has_dual = 0
        best_logistics_dist = 50000.0
        roads.sort(key=lambda x: x[0])
        primary_dist, primary_angle = roads[0]

        for i in range(1, len(roads)):
            sec_dist, sec_angle = roads[i]
            angle_diff = abs(primary_angle - sec_angle)
            if angle_diff > 180: angle_diff = 360 - angle_diff
            if 90 <= angle_diff <= 180:
                has_dual = 1 
                best_logistics_dist = max(primary_dist, sec_dist) 
                break
        dual_access_dict[pt_id] = (1, best_logistics_dist) if has_dual else (0, primary_dist)

    arcpy.management.AddField(sj_out_fc, "Road_Dist_m", "DOUBLE")
    arcpy.management.AddField(sj_out_fc, "Bldg_Dist_m", "DOUBLE")
    arcpy.management.AddField(sj_out_fc, "Dual_Access", "SHORT")
    arcpy.management.AddField(sj_out_fc, "NDVI_Val", "DOUBLE")
    
    merit_flow_layer = "MERIT_Flow_Layer"
    if arcpy.Exists(merit_tif):
        try: arcpy.management.MakeRasterLayer(merit_tif, merit_flow_layer, band_index="3")
        except Exception: arcpy.management.MakeRasterLayer(merit_tif + "\\Band_3", merit_flow_layer)
    else:
        merit_flow_layer = None
    
    log_debug(" -> Extracting values from multi-band Raster Maps...")
    extract_list = [[slope_path, "Slope_Pct"], [curv_path, "Curvature_Val"], [dem_path, "Height_m"], 
                    [red_band, "B04_RED"], [nir_band, "B08_NIR"]]
                    
    if merit_flow_layer: extract_list.append([merit_flow_layer, "Upstream_Flow"])
    if viewshed_enemy: extract_list.append([viewshed_enemy, "Enemy_Vis"])
    if viewshed_friendly: extract_list.append([viewshed_friendly, "Our_Vis"])
    if arcpy.Exists(LANDCOVER_TIF): extract_list.append([LANDCOVER_TIF, "LandCover_ID"])
    if rain_path and arcpy.Exists(rain_path): extract_list.append([rain_path, "Total_Rain_mm"])
    if snow_path and arcpy.Exists(snow_path): extract_list.append([snow_path, "Snow_Cover"])
    if lsi_path and arcpy.Exists(lsi_path): extract_list.append([lsi_path, "LSI_Score"])
    if temp_path and arcpy.Exists(temp_path): extract_list.append([temp_path, "Temp_Val"])
    
    arcpy.sa.ExtractMultiValuesToPoints(sj_out_fc, extract_list, "NONE")
    
    with arcpy.da.UpdateCursor(sj_out_fc, ["OID@", "Road_Dist_m", "Dual_Access", "Bldg_Dist_m", "B04_RED", "B08_NIR", "NDVI_Val"]) as cursor:
        for row in cursor:
            dual_flag, dist_val = dual_access_dict.get(row[0], (0, 50000.0))
            row[1], row[2] = round(dist_val, 2), dual_flag
            b_dist = bldg_dist_dict.get(row[0], -1)
            row[3] = round(b_dist, 2) if b_dist >= 0 else 5000.0 
            red, nir = float(row[4] or 0), float(row[5] or 0)
            row[6] = 0.0 if (nir + red) == 0 else (nir - red) / (nir + red)
            cursor.updateRow(row)
            
    arcpy.management.DeleteField(sj_out_fc, ["B04_RED", "B08_NIR"])
    return sj_out_fc

# ------------------------------------------------------------------------------
# 🧠 MODULE 5: DUAL-BANK FUSION ENGINE & VECTOR BRIDGE GENERATION 
# ------------------------------------------------------------------------------
def run_decision_engine(points_fc, out_folder):
    log_debug("Module 5: Multi-Hazard Target Ranking & Vector Bridge Generation...")

    existing_fields = [f.name for f in arcpy.ListFields(points_fc)]
    has_rain = "Total_Rain_mm" in existing_fields
    has_width = "width_m" in existing_fields
    has_snow = "Snow_Cover" in existing_fields
    has_lsi = "LSI_Score" in existing_fields
    has_temp = "Temp_Val" in existing_fields
    
    read_fields = ["Pair_ID", "Bank_Side", "Road_Dist_m", "Dual_Access", "Bldg_Dist_m", "Slope_Pct", "Curvature_Val", "Height_m", "NDVI_Val", "SHAPE@XY"]
    
    if "Upstream_Flow" in existing_fields: read_fields.append("Upstream_Flow")
    if "Enemy_Vis" in existing_fields: read_fields.append("Enemy_Vis")
    if "Our_Vis" in existing_fields: read_fields.append("Our_Vis")
    if has_rain: read_fields.append("Total_Rain_mm")
    if has_width: read_fields.append("width_m")
    if has_snow: read_fields.append("Snow_Cover")
    if has_lsi: read_fields.append("LSI_Score")
    if has_temp: read_fields.append("Temp_Val")

    max_dist, min_ndvi, max_ndvi, min_flow, max_flow = 0.1, 999.0, -999.0, 99999999.0, -1.0
    min_elev, max_elev, min_rain, max_rain, min_width, max_width = 99999.0, -99999.0, 9999.0, -1.0, 9999.0, -1.0
    min_temp, max_temp = 999.0, -999.0
    
    total_valid_width = 0.0
    valid_width_count = 0

    with arcpy.da.SearchCursor(points_fc, read_fields) as cur:
        for row in cur:
            d, n, e = row[2] or 0, row[8] or 0, row[7] or 0
            f = row[read_fields.index("Upstream_Flow")] if "Upstream_Flow" in read_fields and row[read_fields.index("Upstream_Flow")] else 0
            r = row[read_fields.index("Total_Rain_mm")] if has_rain and row[read_fields.index("Total_Rain_mm")] else 0
            w = row[read_fields.index("width_m")] if has_width and row[read_fields.index("width_m")] else 0
            t = row[read_fields.index("Temp_Val")] if has_temp and row[read_fields.index("Temp_Val")] else 0

            if w > 0:
                total_valid_width += w
                valid_width_count += 1
                if w < min_width: min_width = w
                if w > max_width: max_width = w

            if d > max_dist: max_dist = d
            if n < min_ndvi: min_ndvi = n
            if n > max_ndvi: max_ndvi = n
            if f < min_flow: min_flow = f
            if f > max_flow: max_flow = f
            if e < min_elev: min_elev = e
            if e > max_elev: max_elev = e
            if r < min_rain: min_rain = r
            if r > max_rain: max_rain = r
            if has_temp:
                if t < min_temp: min_temp = t
                if t > max_temp: max_temp = t

    mean_river_width = total_valid_width / valid_width_count if valid_width_count > 0 else 60.0 
    
    ndvi_range = (max_ndvi - min_ndvi) if (max_ndvi - min_ndvi) > 0 else 1.0
    flow_range = (max_flow - min_flow) if (max_flow - min_flow) > 0 else 1.0
    elev_range = (max_elev - min_elev) if (max_elev - min_elev) > 0 else 1.0
    rain_range = (max_rain - min_rain) if (max_rain - min_rain) > 0 else 1.0
    temp_range = (max_temp - min_temp) if (max_temp - min_temp) > 0 else 1.0

    log_debug(" -> Calculating Flood, Thermal Surge, and Tactical Viability for ALL banks independently...")
    bank_scores = {} 

    with arcpy.da.SearchCursor(points_fc, read_fields) as cursor:
        for row in cursor:
            pid, side, dist, dual_flag, bldg_dist, slope, curv, height, ndvi, xy = row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9]
            
            vis_e = row[read_fields.index("Enemy_Vis")] if "Enemy_Vis" in read_fields else None
            vis_f = row[read_fields.index("Our_Vis")] if "Our_Vis" in read_fields else None
            flow  = row[read_fields.index("Upstream_Flow")] if "Upstream_Flow" in read_fields and row[read_fields.index("Upstream_Flow")] else 0
            rain  = row[read_fields.index("Total_Rain_mm")] if has_rain and row[read_fields.index("Total_Rain_mm")] else 0
            width = row[read_fields.index("width_m")] if has_width and row[read_fields.index("width_m")] else 0
            lsi   = row[read_fields.index("LSI_Score")] if has_lsi and row[read_fields.index("LSI_Score")] else 0.0
            
            if has_temp:
                temp = row[read_fields.index("Temp_Val")] if row[read_fields.index("Temp_Val")] is not None else min_temp
            else:
                temp = min_temp

            e_val, f_val = vis_e or 0, vis_f or 0
            
            safe_slope  = slope if slope is not None else (MAX_SLOPE_PERCENT * 2.0)
            safe_height = height if height is not None else min_elev
            safe_ndvi   = ndvi if ndvi is not None else min_ndvi
            safe_rain   = rain if rain is not None else 0.0
            safe_dist   = dist if dist is not None and dist >= 0 else max_dist
            safe_bldg   = bldg_dist if bldg_dist is not None and bldg_dist >= 0 else 5000.0
            safe_width  = width if width is not None and width > 0 else mean_river_width

            norm_temp = (temp - min_temp) / temp_range if temp_range > 0 else 0.0

            flood_risk_factor = 0.0
            if has_rain and safe_rain > 0:
                norm_f_rain  = (safe_rain - min_rain) / rain_range
                norm_f_elev  = 1.0 - ((safe_height - min_elev) / elev_range) 
                norm_f_ndvi  = 1.0 - ((safe_ndvi - min_ndvi) / ndvi_range)   
                norm_f_slope = 1.0 / (safe_slope + 0.01) 
                
                flood_risk = (norm_f_rain * W_FLOOD_RAIN) + (norm_f_elev * W_FLOOD_ELEV) + \
                             (norm_f_ndvi * W_FLOOD_NDVI) + (norm_f_slope * W_FLOOD_SLOPE)
                
                snow_val = row[read_fields.index("Snow_Cover")] if has_snow and row[read_fields.index("Snow_Cover")] else 0.0
                if has_snow and snow_val > 10.0 and has_temp:
                    flood_risk += (norm_temp * 0.3) 
                    flood_risk *= 1.5               
                    
                flood_risk_factor = min(flood_risk, 1.0)

            landslide_risk_factor = min(lsi, 1.0)

            norm_logistics = max(0.0, 1.0 - (safe_dist / max_dist)) 
            norm_safety    = max(0.0, 1.0 - (safe_slope / MAX_SLOPE_PERCENT))
            norm_camo      = (safe_ndvi - min_ndvi) / ndvi_range 
            norm_conceal   = 1.0 if e_val == 0 else 0.0
            
            base_score = (norm_camo * W_CONCEALMENT) + (norm_logistics * W_LOGISTICS) + \
                         (norm_safety * W_SAFETY) + (norm_conceal * W_CONCEALMENT)

            base_score -= max(flood_risk_factor, landslide_risk_factor)
            
            if dual_flag == 0: base_score *= 0.25 
            if safe_bldg < 50.0: base_score *= 0.50 
            if e_val == 0 and f_val > 0: base_score *= 2.0
            elif e_val == 0: base_score *= 1.5

            base_score = max(0.001, base_score)
            cross_cost = 10.0 / base_score

            if pid not in bank_scores: bank_scores[pid] = {}
            bank_scores[pid][side] = {
                "Score": base_score, 
                "XY": xy, 
                "Width": safe_width,
                "CrossCost": cross_cost
            }

    arcpy.ClearWorkspaceCache_management()

    fused_candidates = []
    for pid, sides in bank_scores.items():
        if "LEFT" in sides and "RIGHT" in sides:
            fused_score = (sides["LEFT"]["Score"] + sides["RIGHT"]["Score"]) / 2.0
            avg_width = (sides["LEFT"]["Width"] + sides["RIGHT"]["Width"]) / 2.0
            avg_cost = (sides["LEFT"]["CrossCost"] + sides["RIGHT"]["CrossCost"]) / 2.0
            
            mid_x = (sides["LEFT"]["XY"][0] + sides["RIGHT"]["XY"][0]) / 2.0
            mid_y = (sides["LEFT"]["XY"][1] + sides["RIGHT"]["XY"][1]) / 2.0
            
            fused_candidates.append({
                "PID": pid,
                "Score": fused_score,
                "Mid_XY": (mid_x, mid_y),
                "Left_XY": sides["LEFT"]["XY"],
                "Right_XY": sides["RIGHT"]["XY"],
                "Width": avg_width,
                "Cost": avg_cost
            })

    fused_candidates.sort(key=lambda x: x["Score"], reverse=True)

    selected_bridges = []
    for cand in fused_candidates:
        too_close = False
        for sel in selected_bridges:
            if math.hypot(cand["Mid_XY"][0] - sel["Mid_XY"][0], cand["Mid_XY"][1] - sel["Mid_XY"][1]) < MIN_SEPARATION_METERS:
                too_close = True
                break
        if not too_close:
            selected_bridges.append(cand)
            if len(selected_bridges) == TARGET_BRIDGE_COUNT: break

    log_debug(" -> Rendering Vector Polylines spanning the river banks to eliminate pinch-points...")
    sr = arcpy.Describe(points_fc).spatialReference
    
    top10_fc = os.path.join(SCRATCH_GDB, f"Internal_Top10_Vector_Bridges_{RUN_ID}")
    arcpy.management.CreateFeatureclass(SCRATCH_GDB, f"Internal_Top10_Vector_Bridges_{RUN_ID}", "POLYLINE", spatial_reference=sr)
    arcpy.management.AddField(top10_fc, "BridgeClass", "TEXT")
    arcpy.management.AddField(top10_fc, "Brg_Cost", "DOUBLE")
    arcpy.management.AddField(top10_fc, "Tac_Score", "DOUBLE")
    arcpy.management.AddField(top10_fc, "Span_Width", "DOUBLE")

    with arcpy.da.InsertCursor(top10_fc, ["SHAPE@", "BridgeClass", "Brg_Cost", "Tac_Score", "Span_Width"]) as cur:
        for i, brg in enumerate(selected_bridges):
            rank_str = f"RANK_{i+1:02d}"
            
            p1 = arcpy.Point(brg["Left_XY"][0], brg["Left_XY"][1])
            p2 = arcpy.Point(brg["Right_XY"][0], brg["Right_XY"][1])
            line_array = arcpy.Array([p1, p2])
            poly = arcpy.Polyline(line_array, sr)
            
            cur.insertRow([poly, rank_str, round(brg["Cost"], 2), round(brg["Score"], 3), round(brg["Width"], 2)])

    log_debug(f" -> Creating isolated Feature Classes for Top {TARGET_BRIDGE_COUNT} Vector Bridges...")
    bridges_gdb_name = f"06_Priority_Vector_Bridges_{RUN_ID}.gdb"
    bridges_gdb = os.path.join(out_folder, bridges_gdb_name)
    arcpy.management.CreateFileGDB(out_folder, bridges_gdb_name)

    bridge_field = "BridgeClass"
    with arcpy.da.SearchCursor(top10_fc, [bridge_field]) as cur:
        for row in cur:
            b_class = row[0]
            single_bridge_fc = os.path.join(bridges_gdb, f"Site_{b_class}")
            query = f"{bridge_field} = '{b_class}'"
            arcpy.analysis.Select(top10_fc, single_bridge_fc, query)

    log_debug(f"✅ Top {TARGET_BRIDGE_COUNT} Vector Deployment Sites Isolated into GDB: {bridges_gdb_name}")
    return top10_fc

# ------------------------------------------------------------------------------
# 🔭 MODULE 6: TACTICAL OVERWATCH TOWERS (3 Towers per Bridge)
# ------------------------------------------------------------------------------
def generate_surveillance_towers(top_bridges_fc, dem_path, out_folder):
    log_debug("Module 6: Generating exactly 3 Triangulated Overwatch Towers each for RANK_01 and RANK_02...")
    
    towers_shp = os.path.join(out_folder, f"07_Tactical_Overwatch_Towers_{RUN_ID}.shp")
    spatial_ref = arcpy.Describe(top_bridges_fc).spatialReference
    arcpy.management.CreateFeatureclass(out_folder, f"07_Tactical_Overwatch_Towers_{RUN_ID}.shp", "POINT", spatial_reference=spatial_ref)
    
    arcpy.management.AddField(towers_shp, "Target_Brg", "TEXT")
    arcpy.management.AddField(towers_shp, "Tower_Elev", "DOUBLE")
    
    bridge_field = "BridgeClass"
    if "BridgeClas" in [f.name for f in arcpy.ListFields(top_bridges_fc)]: bridge_field = "BridgeClas"
        
    # 🔥 ONLY select Rank 1 and Rank 2 for the tower generation
    arcpy.management.MakeFeatureLayer(top_bridges_fc, "top2_lyr", f"{bridge_field} IN ('RANK_01', 'RANK_02')")
    
    with arcpy.da.InsertCursor(towers_shp, ["SHAPE@", "Target_Brg", "Tower_Elev"]) as ins_cur:
        with arcpy.da.SearchCursor("top2_lyr", ["SHAPE@", bridge_field]) as search_cur:
            for row in search_cur:
                bridge_geom, b_class = row[0], row[1]
                
                temp_bridge = os.path.join(SCRATCH_GDB, f"Temp_TowerBase_{b_class}")
                query = f"{bridge_field} = '{b_class}'"
                arcpy.analysis.Select("top2_lyr", temp_bridge, query)

                arcpy.management.AddField(temp_bridge, "OFFSETB", "DOUBLE")
                arcpy.management.CalculateField(temp_bridge, "OFFSETB", "2.0")
                
                buffer_fc = os.path.join(SCRATCH_GDB, f"Tower_Buffer_{b_class}")
                arcpy.analysis.Buffer(temp_bridge, buffer_fc, f"{TOWER_BUFFER_METERS} Meters")
                
                try:
                    local_dem = ExtractByMask(dem_path, buffer_fc)
                    vs = Viewshed(local_dem, temp_bridge)
                    visible_dem = Con(vs > 0, local_dem)
                    
                    # Convert the entire visible area to points to sort the elevations
                    visible_pts = os.path.join(SCRATCH_GDB, f"VisPts_{b_class}")
                    arcpy.conversion.RasterToPoint(visible_dem, visible_pts, "Value")

                    pts_list = []
                    with arcpy.da.SearchCursor(visible_pts, ["SHAPE@XY", "grid_code", "SHAPE@"]) as pt_cur:
                        for pt_row in pt_cur:
                            pts_list.append((pt_row[0], pt_row[1], pt_row[2]))

                    # Sort by highest elevation
                    pts_list.sort(key=lambda x: x[1], reverse=True)

                    towers_added = 0
                    selected_towers = []
                    for pt in pts_list:
                        # 🔥 Ensure at least 100m separation between towers so they don't cluster
                        too_close = False
                        for sel_pt in selected_towers:
                            dist = math.hypot(pt[0][0] - sel_pt[0][0], pt[0][1] - sel_pt[0][1])
                            if dist < 100:
                                too_close = True
                                break
                                
                        if not too_close:
                            selected_towers.append(pt)
                            ins_cur.insertRow((pt[2], b_class, pt[1]))
                            towers_added += 1
                            if towers_added == 3: # Stop exactly at 3 towers
                                break
                except Exception as e:
                    log_debug(f"    ⚠️ Failed to generate towers for {b_class}: {e}")

# ------------------------------------------------------------------------------
# 🚛 MODULE 7: PURE OFF-ROAD PATHFINDER & DETOUR CALCULATOR (VECTOR UPGRADE)
# ------------------------------------------------------------------------------
def run_convoy_routing(start_shp, target_shp, top_bridges_fc, slope_raster, ndvi_raster, river_shp, out_folder):
    log_debug("Module 7: Initializing Pure Off-Road Tactical Pathfinder...")
    
    if not (arcpy.Exists(start_shp) and arcpy.Exists(target_shp)):
        log_debug("⚠️ Start or Target SHP missing. Bypassing Convoy Routing.")
        return

    sr = arcpy.Describe(start_shp).spatialReference
    arcpy.env.extent = slope_raster
    arcpy.env.snapRaster = slope_raster
    arcpy.env.cellSize = slope_raster

    log_debug(" -> Compiling PURE OFF-ROAD Tactical Friction Surface (Roads Ignored)...")
    
    friction_slope = Con(Raster(slope_raster) < 5, 8, Con(Raster(slope_raster) < 15, 15, 50))
    camo_mod = Con(Raster(ndvi_raster) > 0.4, -5, Con(Raster(ndvi_raster) < 0.1, 5, 0))
    base_friction = Con((friction_slope + camo_mod) < 1, 1, friction_slope + camo_mod)

    river_oid_field = arcpy.Describe(river_shp).OIDFieldName
    river_rast = os.path.join(SCRATCH_GDB, f"Rasterized_Rivers_{RUN_ID}")
    arcpy.conversion.PolylineToRaster(river_shp, river_oid_field, river_rast, cellsize=slope_raster)
    
    master_friction = Con(IsNull(river_rast), base_friction, 1000000)
    
    bridge_field = "BridgeClass"
    if "BridgeClas" in [f.name for f in arcpy.ListFields(top_bridges_fc)]: bridge_field = "BridgeClas"

    start_pt, target_pt = None, None
    with arcpy.da.SearchCursor(start_shp, ["SHAPE@XY"]) as cursor:
        for row in cursor: start_pt = row[0]; break
    with arcpy.da.SearchCursor(target_shp, ["SHAPE@XY"]) as cursor:
        for row in cursor: target_pt = row[0]; break

    log_debug(" -> Executing massive-scale CostDistance from Base and Target (1x Operation)...")
    c_dist_s = os.path.join(SCRATCH_GDB, f"CD_Start_Base_{RUN_ID}")
    c_back_s = os.path.join(SCRATCH_GDB, f"BL_Start_Base_{RUN_ID}")
    CostDistance(start_shp, master_friction, out_backlink_raster=c_back_s).save(c_dist_s)
    
    c_dist_t = os.path.join(SCRATCH_GDB, f"CD_Target_Base_{RUN_ID}")
    c_back_t = os.path.join(SCRATCH_GDB, f"BL_Target_Base_{RUN_ID}")
    CostDistance(target_shp, master_friction, out_backlink_raster=c_back_t).save(c_dist_t)

    route_legs_start, route_legs_target, route_spans = [], [], []
    report_data = []

    with arcpy.da.SearchCursor(top_bridges_fc, ["SHAPE@", bridge_field, "Span_Width"]) as cursor:
        for row in cursor:
            geom, b_class, span_width = row[0], row[1], row[2]
            
            p1 = geom.firstPoint
            p2 = geom.lastPoint
            
            dist_p1_s = math.hypot(start_pt[0] - p1.X, start_pt[1] - p1.Y)
            dist_p2_s = math.hypot(start_pt[0] - p2.X, start_pt[1] - p2.Y)
            
            if dist_p1_s < dist_p2_s:
                start_bank_pt = p1
                target_bank_pt = p2
            else:
                start_bank_pt = p2
                target_bank_pt = p1
            
            log_debug(f" -> Forging {b_class} Vector Corridor (Eliminating hourglass pinch-point)...")
            
            leg1_fc = os.path.join(SCRATCH_GDB, f"Bank_S_{b_class}")
            arcpy.management.CopyFeatures([arcpy.PointGeometry(start_bank_pt, sr)], leg1_fc)
            
            leg2_fc = os.path.join(SCRATCH_GDB, f"Bank_T_{b_class}")
            arcpy.management.CopyFeatures([arcpy.PointGeometry(target_bank_pt, sr)], leg2_fc)
            
            temp_bridge = os.path.join(SCRATCH_GDB, f"Temp_Door_{b_class}")
            query = f"{bridge_field} = '{b_class}'"
            arcpy.analysis.Select(top_bridges_fc, temp_bridge, query)
            route_spans.append(temp_bridge)
            
            p_rast_s = CostPath(leg1_fc, c_dist_s, c_back_s, "BEST_SINGLE", arcpy.Describe(leg1_fc).OIDFieldName)
            r_vec_s = os.path.join(SCRATCH_GDB, f"Leg_S_{b_class}")
            arcpy.conversion.RasterToPolyline(p_rast_s, r_vec_s, "ZERO", 0, "SIMPLIFY")
            arcpy.management.AddField(r_vec_s, "Brg_Rnk", "TEXT")
            arcpy.management.CalculateField(r_vec_s, "Brg_Rnk", f"'{b_class}'")
            route_legs_start.append(r_vec_s)

            p_rast_t = CostPath(leg2_fc, c_dist_t, c_back_t, "BEST_SINGLE", arcpy.Describe(leg2_fc).OIDFieldName)
            r_vec_t = os.path.join(SCRATCH_GDB, f"Leg_T_{b_class}")
            arcpy.conversion.RasterToPolyline(p_rast_t, r_vec_t, "ZERO", 0, "SIMPLIFY")
            arcpy.management.AddField(r_vec_t, "Brg_Rnk", "TEXT")
            arcpy.management.CalculateField(r_vec_t, "Brg_Rnk", f"'{b_class}'")
            route_legs_target.append(r_vec_t)
            
            dist_s = math.hypot(start_pt[0] - start_bank_pt.X, start_pt[1] - start_bank_pt.Y)
            dist_t = math.hypot(target_pt[0] - target_bank_pt.X, target_pt[1] - target_bank_pt.Y)
            disp_total = (dist_s / 1000.0) + (dist_t / 1000.0)
            
            dist_act_s = sum(row[0] for row in arcpy.da.SearchCursor(r_vec_s, ["SHAPE@LENGTH"])) / 1000.0
            dist_act_t = sum(row[0] for row in arcpy.da.SearchCursor(r_vec_t, ["SHAPE@LENGTH"])) / 1000.0
            dist_total = dist_act_s + dist_act_t + (span_width / 1000.0) 
            
            detour_idx = dist_total / disp_total if disp_total > 0 else 1.0
            
            report_data.append({
                "Rank": b_class,
                "Disp_Total_KM": round(disp_total, 2),
                "Dist_Total_KM": round(dist_total, 2),
                "Detour_Index": round(detour_idx, 2),
                "Leg1_Dist": round(dist_act_s, 2),
                "Leg2_Dist": round(dist_act_t, 2)
            })

            arcpy.ClearWorkspaceCache_management()

    log_debug(" -> Compiling Isolated Routes into Dedicated Final Geodatabase...")
    
    final_gdb_name = f"08_Final_Assault_Routes_{RUN_ID}.gdb"
    final_gdb = os.path.join(out_folder, final_gdb_name)
    arcpy.management.CreateFileGDB(out_folder, final_gdb_name)

    for i in range(len(route_legs_start)):
        b_class = report_data[i]["Rank"]
        indiv_route = os.path.join(final_gdb, f"Route_{b_class}")
        
        arcpy.management.Merge([route_legs_start[i], route_spans[i], route_legs_target[i]], indiv_route)
        
        arcpy.management.AddField(indiv_route, "Total_Dist", "DOUBLE")
        arcpy.management.CalculateField(indiv_route, "Total_Dist", report_data[i]["Dist_Total_KM"])
        arcpy.management.AddField(indiv_route, "Detour_Idx", "DOUBLE")
        arcpy.management.CalculateField(indiv_route, "Detour_Idx", report_data[i]["Detour_Index"])

    print("\n" + "="*80)
    print("📊 TACTICAL CONVOY INTELLIGENCE REPORT")
    print("="*80)
    print(f"{'ROUTE (BRIDGE)':<15} | {'STRAIGHT LINE (KM)':<18} | {'ACTUAL ROUTE (KM)':<18} | {'DETOUR RATING'}")
    print("-" * 80)
    
    report_data.sort(key=lambda x: x["Detour_Index"])
    
    for rd in report_data:
        rating = "🟢 OPTIMAL" if rd['Detour_Index'] < 1.5 else "🟡 MODERATE" if rd['Detour_Index'] < 2.5 else "🔴 SEVERE DETOUR"
        
        if rd['Detour_Index'] >= MAX_DETOUR_INDEX:
            print(f"{rd['Rank']:<15} | {rd['Disp_Total_KM']:<18} | {rd['Dist_Total_KM']:<18} | {rd['Detour_Index']} (🔴 FLAGGED: >= 1.5)")
        else:
            print(f"{rd['Rank']:<15} | {rd['Disp_Total_KM']:<18} | {rd['Dist_Total_KM']:<18} | {rd['Detour_Index']} ({rating})")
            
    print("="*80 + "\n")

    log_debug(f"✅ Logistics Web mathematically locked! Individual routes saved to: {final_gdb}")

# ==============================================================================
# 🚀 MAIN EXECUTION BLOCK
# ==============================================================================
if __name__ == "__main__":
    
    print("="*60)
    print("🚀 SYSTEM INITIATED: Wargaming Operational Pathfinder")
    print(f"🕒 RUN_ID: {RUN_ID}")
    print("-" * 60)
    print("📋 MISSION BRIEFING:")
    print("   📍 Target Area: Indus River, Kargil Sector")
    print("   🏗️ Operation: Combat Bridge Deployment & Maneuver Pathfinding")
    print("   ⏳ Window: 40-Day operational deployment")
    print("   🚛 Logistics: Optimizing for Heavy Armored Vehicle Crossings")
    print("   ⛰️ Hazards: Geotechnical LSI (Sand/Clay/Temp) + Flood Models Active")
    print("   🏘️ Clearance: Urban/Building Chokepoint Avoidance Active")
    print("   ❄️ Snowmelt Surge Protocol: ARMED (MODIS Temp Multiplier Active)")
    print("   🛣️ Strategy: PURE OFF-ROAD ROUTING (Road Magnetism DISABLED)")
    print("   🌉 Deployment: Dual-Bank Recon & Physical Vector Bridge Spans")
    print("   📡 Overwatch: Triangulated Networks (Rank 1 & 2 = 3x Towers Each)")
    print("   📊 Intelligence: Detour Calculated, All Routes Retained for Review")
    print("   📁 Output: Isolated Feature Classes generated in dedicated GDB")
    print("="*60)
    
    if validate_inputs():
        loc_riv, loc_rd, loc_bldg, slope_path, curv_path, ndvi_path = extract_theater_and_terrain(OUTPUT_DIR)
        
        candidates_fc = generate_dual_bank_candidates(loc_riv)
        
        rain_path = process_climatology(RAIN_START_DATE, RAIN_END_DATE, OUTPUT_DIR)
        
        lsi_path = generate_landslide_hazard_map(slope_path, rain_path, CLAY_TIF, SAND_TIF, TEMP_TIF, OUTPUT_DIR)
        
        enriched_pts = extract_spatial_intel(candidates_fc, DEM_PATH, slope_path, curv_path, MERIT_TIF, TEMP_TIF, rain_path, MODIS_SNOW, lsi_path, loc_bldg, S2_B04_RED, S2_B08_NIR, OUTPUT_DIR)
        
        top10_fc = run_decision_engine(enriched_pts, OUTPUT_DIR)
        
        generate_surveillance_towers(top10_fc, DEM_PATH, OUTPUT_DIR)
        
        run_convoy_routing(START_SHP, TARGET_SHP, top10_fc, slope_path, ndvi_path, loc_riv, OUTPUT_DIR)

        print("="*60)
        log_debug(f"🏁 PIPELINE COMPLETE. All tactical intelligence extracted to {OUTPUT_DIR}.")
        print("="*60)
    else:
        log_debug("❌ PIPELINE HALTED: Please resolve the missing files listed above.")

    arcpy.CheckInExtension("Spatial")
