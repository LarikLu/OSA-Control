
# AQ6315E Optical Spectrum Analyzer (OSA) Controller

This project provides a Python-based automation tool for controlling the **ANDO AQ6315E Optical Spectrum Analyzer** via GPIB interface. It enables high-resolution, multi-segment spectral scanning, data logging, and plot generation.

---

## Maintainer
Larik Lu - Cundiff Lab - University of Michigan

First Edition: March 2025


## Features

- GPIB-based control using PyVISA
- Customizable wavelength sweep (start, stop, step)
- Resolution, averaging, and sensitivity settings
- Linear scale acquisition in **μW/nm**
- Automatic data saving to timestamped folders
- Output as both `.csv` and `.png`
- Logging of parameters and scan status

---

## Requirements

- Python ≥ 3.10
- GPIB interface (e.g. NI GPIB-USB-HS)
- ANDO AQ6315E (tested)
- Libraries:

```bash
pip install pyvisa matplotlib
```

---

## Usage

Run directly:

    python osa_control.py

The script will:

1. Connect to the AQ6315E at `GPIB0::20::INSTR`.  
   *(Make sure the correct GPIB address is used; you can check available ports with `pyvisa.ResourceManager().list_resources()`.)*

2. Configure measurement parameters, including:
   - Resolution
   - Sensitivity
   - Averaging count
   - Reference level (manual or auto)
   - Power scale (linear)
   - Unit (μW/nm)

3. Sweep over the specified wavelength range in segments (if needed).

4. Save the following files into a timestamped output folder:

   - `osa_trace.csv` — exported spectrum data
   - `osa_plot.png` — plotted spectrum image
   - `osa_run.log` — log file containing parameters and execution status

All output is saved under:

    ./YYYY-MM-DD/run_XXXX/

---

## Configuration

Update the parameters in the AQ6315EController class instantiation (typically at the bottom of osa_control.py):

    controller = AQ6315EController(
        gpib_address='GPIB0::20::INSTR',
        sensitivity='SNAT',
        start_wavelength=1525,
        stop_wavelength=1625,
        step_size=5,
        use_auto_reference=True,
        reference_level_nw=12.0,
        resolution_nm=0.05,
        averaging_count=5
    )

---

## Output Folder Structure

    2025-03-31/
    └── run_0001/
        ├── osa_trace.csv       ← Saved spectral data
        ├── osa_plot.png        ← Plot of spectrum
        └── osa_run.log         ← Parameter and scan log

---

## Sample Log

    [2025-03-31 05:43:36] OSA successfully configured.
    [2025-03-31 05:43:36] Start: 1525 nm, Stop: 1625 nm, Step: 5 nm
    [2025-03-31 05:43:36] Resolution: 0.05 nm, Averaging: 5, Sensitivity: SNAT
    [2025-03-31 05:43:36] Reference: AUTO
    [2025-03-31 05:43:36] Scale: Linear, Units: μW/nm
    [2025-03-31 05:43:36] Starting scan loop...
    [2025-03-31 05:46:42] Scan loop completed.
    [2025-03-31 05:46:43] Data saved: C:\Users\...

---

## Notes

- Tested with **ANDO AQ6315E**, firmware version **MR06.14**
- Data is acquired in **linear scale** with units of **μW/nm**  
  *(You may modify the code to adjust units or scale settings if needed)*
- GPIB communication requires a properly installed NI-VISA driver and GPIB interface (e.g., NI GPIB-USB-HS)
- For multi-user environments or long-term archival, consider adding metadata fields or parsing instrument ID automatically
---

## Developer Tips

- Use git and .gitignore to manage virtual environments, data, and temp files
- Keep parameter configurations at the top or in config.yaml if extending
- Use Python logging module for more advanced logging needs