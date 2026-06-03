# Combined flat robot telemetry. One atomic snapshot per tick.
# Foxglove Plot: add series "/telemetry.<field>" — every field is a plain number.
std_msgs/Header header

# --- UPS (INA219, read over I2C) ---
float32 ups_bus_voltage_v      # load-side bus voltage, volts
float32 ups_current_a          # current, amps (negative=charging, positive=discharging)
float32 ups_power_w            # power, watts
float32 ups_percent            # battery charge estimate, percent 0-100 (3S LiPo linear, ±20%)

# --- OAK device (depthai). Sourced by subscribing to /telemetry/oak (OakStats). ---
float32 oak_fps                # frames per second over the reporting window
float32 oak_chip_temp_c        # device average chip temperature, Celsius
uint8   oak_usb_speed          # negotiated link gen: 2=USB2/high, 3=USB3/super, 0=unknown
float32 oak_cmx_mem_used_mb    # CMX memory in use, megabytes
float32 oak_ddr_mem_used_mb    # DDR memory in use, megabytes
float32 oak_leon_css_cpu_pct   # Leon CSS core CPU usage, percent
float32 oak_leon_mss_cpu_pct   # Leon MSS core CPU usage, percent
float32 oak_pipeline_get_ms    # mean blocking wait on device queue get(), ms
float32 oak_tracker_ms         # mean tracker update time, ms
float32 oak_iter_ms            # mean full inference-loop iteration time, ms

# --- Host / Pi (read from /proc and /sys) ---
float32 pi_cpu_temp_c          # host CPU temperature, Celsius (thermal_zone0)
float32 pi_cpu_pct             # host CPU usage since last tick, percent (/proc/stat)
float32 pi_mem_used_mb         # host memory in use (MemTotal-MemAvailable), megabytes
float32 pi_uptime_s            # host uptime since boot, seconds (/proc/uptime)
