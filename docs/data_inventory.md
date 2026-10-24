# GlycoTwin Phase 0: Data Inventory

## 1. Environment & Paths

The local workspace was inspected on Windows PowerShell without assumptions regarding directory structure.

- **Workspace Root**: `c:\Users\gupta\Desktop\GlycoTwin`
- **HUPA-UCM Dataset Root**: `c:\Users\gupta\Desktop\GlycoTwin\HUPA-UCM Diabetes Dataset`
- **Glucose-ML-Project Root**: `c:\Users\gupta\Desktop\GlycoTwin\Glucose-ML-Project-main`

---

## 2. Overall Directory Classification

| Directory | Total Files | Primary Functional Classification | Description |
| :--- | :--- | :--- | :--- |
| `HUPA-UCM Diabetes Dataset/` | 5,697 files | Data (CGM, Insulin, Wearables) | Primary research cohort dataset (Hidalgo et al., 2024). |
| `Glucose-ML-Project-main/` | 2,418 files | Code, Documentation & Curated Metadata | Multi-dataset benchmark suite by Augmented Health Lab (Prioleau et al., 2025/2026). |

---

## 3. Detailed File Breakdown: HUPA-UCM Diabetes Dataset

The dataset is organized into two primary subdirectories: `Preprocessed/` and `Raw_Data/`.

### A. Preprocessed Files (`HUPA-UCM Diabetes Dataset/HUPA-UCM Diabetes Dataset/Preprocessed/`)
Contains 25 files formatted as semicolon-delimited CSVs on a uniform 5-minute sampling grid.

| Relative File Path | Size (Bytes) | Extension | Classification | Modalities Included |
| :--- | :--- | :--- | :--- | :--- |
| `Preprocessed/HUPA0001P.csv` | 360,458 | `.csv` | Data | CGM, Basal, Bolus, Carbs, Steps, Cals, HR |
| `Preprocessed/HUPA0002P.csv` | 294,858 | `.csv` | Data | CGM, Basal, Bolus, Carbs, Steps, Cals, HR |
| `Preprocessed/HUPA0003P.csv` | 359,903 | `.csv` | Data | CGM, Basal, Bolus, Carbs, Steps, Cals, HR |
| `Preprocessed/HUPA0004P.csv` | 309,348 | `.csv` | Data | CGM, Basal, Bolus, Carbs, Steps, Cals, HR |
| `Preprocessed/HUPA0005P.csv` | 358,712 | `.csv` | Data | CGM, Basal, Bolus, Carbs, Steps, Cals, HR |
| `Preprocessed/HUPA0006P.csv` | 213,457 | `.csv` | Data | CGM, Basal, Bolus, Carbs, Steps, Cals, HR |
| `Preprocessed/HUPA0007P.csv` | 371,751 | `.csv` | Data | CGM, Basal, Bolus, Carbs, Steps, Cals, HR |
| `Preprocessed/HUPA0009P.csv` | 356,416 | `.csv` | Data | CGM, Basal, Bolus, Carbs, Steps, Cals, HR |
| `Preprocessed/HUPA0010P.csv` | 281,983 | `.csv` | Data | CGM, Basal, Bolus, Carbs, Steps, Cals, HR |
| `Preprocessed/HUPA0011P.csv` | 303,513 | `.csv` | Data | CGM, Basal, Bolus, Carbs, Steps, Cals, HR |
| `Preprocessed/HUPA0014P.csv` | 314,109 | `.csv` | Data | CGM, Basal, Bolus, Carbs, Steps, Cals, HR |
| `Preprocessed/HUPA0015P.csv` | 296,381 | `.csv` | Data | CGM, Basal, Bolus, Carbs, Steps, Cals, HR |
| `Preprocessed/HUPA0016P.csv` | 383,590 | `.csv` | Data | CGM, Basal, Bolus, Carbs, Steps, Cals, HR |
| `Preprocessed/HUPA0017P.csv` | 309,028 | `.csv` | Data | CGM, Basal, Bolus, Carbs, Steps, Cals, HR |
| `Preprocessed/HUPA0018P.csv` | 302,156 | `.csv` | Data | CGM, Basal, Bolus, Carbs, Steps, Cals, HR |
| `Preprocessed/HUPA0019P.csv` | 315,725 | `.csv` | Data | CGM, Basal, Bolus, Carbs, Steps, Cals, HR |
| `Preprocessed/HUPA0020P.csv` | 241,144 | `.csv` | Data | CGM, Basal, Bolus, Carbs, Steps, Cals, HR |
| `Preprocessed/HUPA0021P.csv` | 198,863 | `.csv` | Data | CGM, Basal, Bolus, Carbs, Steps, Cals, HR |
| `Preprocessed/HUPA0022P.csv` | 378,037 | `.csv` | Data | CGM, Basal, Bolus, Carbs, Steps, Cals, HR |
| `Preprocessed/HUPA0023P.csv` | 332,365 | `.csv` | Data | CGM, Basal, Bolus, Carbs, Steps, Cals, HR |
| `Preprocessed/HUPA0024P.csv` | 248,359 | `.csv` | Data | CGM, Basal, Bolus, Carbs, Steps, Cals, HR |
| `Preprocessed/HUPA0025P.csv` | 379,238 | `.csv` | Data | CGM, Basal, Bolus, Carbs, Steps, Cals, HR |
| `Preprocessed/HUPA0026P.csv` | 3,354,069 | `.csv` | Data | CGM, Basal, Bolus, Carbs, Steps, Cals, HR |
| `Preprocessed/HUPA0027P.csv` | 14,054,763 | `.csv` | Data | CGM, Basal, Bolus, Carbs, Steps, Cals, HR |
| `Preprocessed/HUPA0028P.csv` | 2,193,712 | `.csv` | Data | CGM, Basal, Bolus, Carbs, Steps, Cals, HR |

### B. Raw Data Files (`HUPA-UCM Diabetes Dataset/HUPA-UCM Diabetes Dataset/Raw_Data/`)
Contains 5,761 files organized by participant directory (`HUPA0001P` to `HUPA0028P`):
- `fitbit/`: Per-day minute-resolution files for steps, calories, heart rate, and sleep (e.g. `HUPA0001P_cals_YYYY-MM-DD.csv`, `HUPA0001P_hr_YYYY-MM-DD.csv`, `HUPA0028P_sleep_YYYY-MM-DD_night.csv`).
- `free_style_sensor/`: Raw sensor exports from Abbott FreeStyle Libre 2 (`*_free_style_sensor_*.csv`).
- `medtronic_insulin_pump/`: Raw pump logs from Medtronic MiniMed 640G (`*_medtronic_insulin_pump_&_sensor_*.csv`).

---

## 4. Key Files in Glucose-ML-Project-main

| File Path | Size (Bytes) | Classification | Role in Project |
| :--- | :--- | :--- | :--- |
| `README.md` | 8,251 | Documentation | Explains dataset harmonization framework and scripts. |
| `CONTRIBUTING.md` | 2,930 | Documentation | Development standards. |
| `LICENSE` | 1,077 | Documentation | Open-source MIT licence. |
| `dependencies.txt` | 53 | Documentation | Base dependencies: pandas, requests, matplotlib, numpy, scikit-learn. |
| `2_Harmonize-cgm-datasets/HUPA-UCM/HUPA-UCM_extract-glucose-data.py` | 2,743 | Code | Standardizes raw CSVs to uniform schema. |
| `2_Harmonize-cgm-datasets/HUPA-UCM/HUPA-UCM_metadata.py` | 3,162 | Code | Computes participant-level statistics. |
| `2_Harmonize-cgm-datasets/HUPA-UCM/README.md` | 2,128 | Documentation | Explains HUPA-UCM extraction procedures. |
| `3_Glucose-ML-collection/HUPA-UCM/HUPA-UCM-metadata.csv` | 1,911 | Data / Metadata | Clinically curated metadata (age, gender, HbA1c, device). |
| `3_Glucose-ML-collection/HUPA-UCM/HUPA-UCM-from-Glucose-ML.zip` | 1,574,300 | Archive | Pre-packaged harmonized files. |
| `3_Glucose-ML-collection/HUPA-UCM/README.md` | 2,766 | Documentation | DOI, CC BY 4.0 citation, and provenance. |

---

## 5. Storage and Git Handling Rules

- The raw and preprocessed research files are strictly excluded from git tracking via `.gitignore` (`HUPA-UCM Diabetes Dataset/`, `data/raw/*`, `data/processed/*`).
- Only minimal sample fixtures without protected health information are stored in `data/sample/` for testing purposes.
