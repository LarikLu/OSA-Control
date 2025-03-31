import os
import time
import datetime
import csv
import matplotlib.pyplot as plt
import pyvisa


class AQ6315EController:
    def __init__(self,
                 gpib_address='GPIB0::20::INSTR',
                 sensitivity='SNAT',
                 start_wavelength=1525,
                 stop_wavelength=1625,
                 step_size=5,
                 use_auto_reference=True,
                 reference_level_nw=12.0,
                 resolution_nm=0.05,
                 averaging_count=5):
        self.rm = pyvisa.ResourceManager()
        self.osa = self.rm.open_resource(gpib_address, timeout=10000)  # 10s timeout
        self.sensitivity = sensitivity
        self.start_wavelength = start_wavelength
        self.stop_wavelength = stop_wavelength
        self.step_size = step_size
        self.use_auto_reference = use_auto_reference
        self.reference_level_nw = reference_level_nw
        self.resolution_nm = resolution_nm
        self.averaging_count = averaging_count

    def setup_osa(self):
        """
        Configure OSA before data acquisition.
        """
        try:
            self.osa.write("*IDN?")
            raw_idn = self.osa.read_raw()
            idn = ''.join([chr(b) if 32 <= b <= 126 else '.' for b in raw_idn])
            print(f"Connected to: {idn.strip()}")

            time.sleep(1)

            # self.osa.write("*RST")  # Optional: Resets the instrument.
            # Be cautious—OSA takes a long time to restart, and sending a command too soon may cause a timeout.
            # time.sleep(0.5)  # Adjust the delay carefully to avoid conflicts with the next command.

            self.osa.write(self.sensitivity)
            # self.osa.write("PLSLPF")  # Removed: AQ6315E does not support this command
            # AQ6315E uses linear sweep by default
            resolution_map = {
                0.05: "RESLN0.05",
                0.1: "RESLN0.10",
                0.2: "RESLN0.20",
                0.5: "RESLN0.50",
                1.0: "RESLN1.00",
                2.0: "RESLN2.00",
                5.0: "RESLN5.00",
            }
            cmd = resolution_map.get(self.resolution_nm)
            if cmd:
                print(f"sending command: {cmd}")
                self.osa.query("RESLN?")
                self.osa.write(cmd)
            else:
                raise ValueError(f"Unsupported resolution: {self.resolution_nm}")
            self.osa.write(f"AVCNT {self.averaging_count}")
            self.osa.write("LSCL 0")  # Linear Scale
            self.osa.write("LSUNT 2")  # nW/nm

            if self.use_auto_reference:
                self.osa.write("REFLA")  # Auto reference level
            else:
                self.osa.write(f"REFLU{self.reference_level_nw:.2f}")

            self.osa.write("ACTTRC A")  # Set Trace A as active output trace

            print("OSA configured with sensitivity, resolution, units, and averaging.")
            self.log(self.log_dir, "OSA successfully configured.")
            self.log(self.log_dir,
                     f"Start: {self.start_wavelength} nm, Stop: {self.stop_wavelength} nm, Step: {self.step_size} nm")
            self.log(self.log_dir,
                     f"Resolution: {self.resolution_nm} nm, Averaging: {self.averaging_count}, Sensitivity: {self.sensitivity}")
            self.log(self.log_dir,
                     f"Reference: {'AUTO' if self.use_auto_reference else str(self.reference_level_nw) + ' nW'}")
            self.log(self.log_dir, f"Scale: Linear, Units: μW/nm")

        except pyvisa.VisaIOError as e:
            print(f"VISA communication error during setup: {e}")
            raise

    def log(self, directory, message):
        """
        Append a log message with timestamp to osa_run.log
        """
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_path = os.path.join(directory, "osa_run.log")
        with open(log_path, "a", encoding="utf-8") as logfile:
            logfile.write(f"[{timestamp}] {message}\n")

    def set_wavelength_range(self, start, stop):
        self.osa.write(f"STAWL{start:.2f}")
        self.osa.write(f"STPWL{stop:.2f}")

    def start_sweep_and_wait(self):
        self.osa.write("SGL")
        while int(self.osa.query("SWEEP?")) > 0:
            time.sleep(0.2)

    def get_trace_data(self):
        trace_idx = int(self.osa.query("ACTV?"))  # NEW

        trace = "ABC"[trace_idx]  # NEW
        self.osa.write("LDTDIG3")
        time.sleep(0.5)
        wavelengths = self.osa.query(f"WDAT{trace}").strip().split(',')[1:]
        levels = self.osa.query(f"LDAT{trace}").strip().split(',')[1:]

        return wavelengths, levels

    def run_scan_loop(self):
        current_start = self.start_wavelength
        all_wavelengths = []
        all_levels = []

        self.log(self.log_dir, "Starting scan loop...")
        while current_start < self.stop_wavelength:
            current_stop = min(current_start + self.step_size, self.stop_wavelength)
            self.set_wavelength_range(current_start, current_stop)
            self.start_sweep_and_wait()
            wl, lv = self.get_trace_data()

            if current_stop < self.stop_wavelength:
                wl = wl[:-1]
                lv = lv[:-1]

            all_wavelengths += wl
            all_levels += lv
            current_start += self.step_size

        self.log(self.log_dir, "Scan loop completed.")
        return all_wavelengths, all_levels

    def save_trace(self, wavelengths, levels, directory):
        """
        Save the spectrum data as CSV and plot as PNG.
        """
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        csv_filename = os.path.join(directory, "osa_trace.csv")
        png_filename = os.path.join(directory, "osa_plot.png")

        # Save CSV
        with open(csv_filename, mode='w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["# AQ6315E Spectrum Data"])
            writer.writerow([f"# Timestamp: {now}"])
            writer.writerow([f"# Start: {self.start_wavelength} nm"])
            writer.writerow([f"# Stop: {self.stop_wavelength} nm"])
            writer.writerow([f"# Step size: {self.step_size} nm"])
            writer.writerow([f"# Resolution: {self.resolution_nm} nm"])
            writer.writerow([f"# Averaging count: {self.averaging_count}"])
            writer.writerow([f"# Sensitivity: {self.sensitivity}"])
            writer.writerow(
                [f"# Reference level: {'AUTO' if self.use_auto_reference else str(self.reference_level_nw) + ' nW'}"])
            writer.writerow([f"# Scale: Linear"])
            writer.writerow([f"# Units: μW/nm"])
            writer.writerow([])
            writer.writerow(["Wavelength (nm)", "Level (μW/nm)"])

            for w, l in zip(wavelengths, levels):
                writer.writerow([w, l])
        print(f"CSV data saved to {csv_filename}")

        # Plot and save figure
        float_wl = list(map(float, wavelengths))
        float_lv = list(map(float, levels))

        plt.figure(figsize=(10, 6))
        plt.plot(float_wl, float_lv, lw=1.2)
        plt.title("OSA Spectrum")
        plt.xlabel("Wavelength (nm)")
        plt.ylabel("Level (μW/nm)")
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(png_filename, dpi=300)
        plt.close()

        print(f"Plot saved to {png_filename}")
        self.log(directory, f"Data saved: {csv_filename}, Plot saved: {png_filename}")

def create_output_directory():
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    base_dir = os.path.join(os.getcwd(), today)
    os.makedirs(base_dir, exist_ok=True)
    counter = 1
    while True:
        run_dir = os.path.join(base_dir, f"run_{counter:04d}")
        if not os.path.exists(run_dir):
            os.makedirs(run_dir)
            return run_dir
        counter += 1


if __name__ == "__main__":
    output_dir = create_output_directory()
    controller = AQ6315EController(
        gpib_address='GPIB0::20::INSTR',
        sensitivity='SNAT',
        start_wavelength=1525,
        stop_wavelength=1625,
        step_size=5,
        use_auto_reference=True,
        reference_level_nw=12.0,  # Ignored if auto ref is enabled
        resolution_nm=0.05,
        averaging_count=5
    )

    controller.log_dir = output_dir
    controller.setup_osa()
    wavelengths, levels = controller.run_scan_loop()
    controller.save_trace(wavelengths, levels, output_dir)