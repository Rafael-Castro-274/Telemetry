#só podemos mudar nosssos caminhos, quando mudamos nossas decisões"
"""
Projeto Corredor X
Telemetria ACC (Shared Memory)

Realtime:
- Freio
- Acelerador
- Janela não intrusiva

Offline:
- PDF com gráficos completos da sessão
"""

import mmap
import struct
import time
import csv
import numpy as np
import matplotlib
matplotlib.use("Agg")  # Alterar backend para evitar problemas com interface gráfica

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from collections import deque
from datetime import datetime

# ==========================
# SHARED MEMORY (ACC)
# ==========================

SHM_NAME = "Local\\acpmf_physics"
SHM_SIZE = 4096

OFFSET = {
    "gas": 4,
    "brake": 8,
    "gear": 16,
    "rpm": 20,
    "steer": 24,
    "speed": 28
}

class ACCSharedMemory:
    def __init__(self):
        self.mm = mmap.mmap(-1, SHM_SIZE, tagname=SHM_NAME, access=mmap.ACCESS_READ)

    def read(self):
        self.mm.seek(0)
        data = self.mm.read(SHM_SIZE)

        return {
            "gas":   struct.unpack_from("f", data, OFFSET["gas"])[0],
            "brake": struct.unpack_from("f", data, OFFSET["brake"])[0],
            "gear":  struct.unpack_from("i", data, OFFSET["gear"])[0],
            "rpm":   struct.unpack_from("i", data, OFFSET["rpm"])[0],
            "steer": struct.unpack_from("f", data, OFFSET["steer"])[0],
            "speed": struct.unpack_from("f", data, OFFSET["speed"])[0],
        }

# ==========================
# SESSÃO
# ==========================

SESSION_NAME = datetime.now().strftime("%Y%m%d_%H%M%S")
CSV_FILE = f"telemetry_{SESSION_NAME}.csv"
PDF_FILE = f"telemetry_{SESSION_NAME}.pdf"

def init_csv():
    with open(CSV_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["time", "gas", "brake", "rpm", "gear", "steer", "speed"])

def save_row(t, d):
    with open(CSV_FILE, "a", newline="") as f:
        csv.writer(f).writerow([
            t, d["gas"], d["brake"], d["rpm"],
            d["gear"], d["steer"], d["speed"]
        ])

# ==========================
# BUFFER REALTIME
# ==========================

MAX_POINTS = 300
gas_buf = deque(maxlen=MAX_POINTS)
brake_buf = deque(maxlen=MAX_POINTS)

# ==========================
# JANELA REALTIME (NÃO INTRUSIVA)
# ==========================

plt.ion()
fig, ax = plt.subplots(figsize=(6, 3))
fig.canvas.manager.set_window_title("Corredor X | Realtime")

fig.patch.set_facecolor("black")
ax.set_facecolor("black")

ax.set_ylim(0, 1.05)
ax.set_xlim(0, MAX_POINTS)
ax.set_title("Acelerador & Freio", color="white")

line_gas, = ax.plot([], [], color="red", linewidth=2)
line_brake, = ax.plot([], [], color="lime", linewidth=2)

ax.tick_params(colors="white")
for spine in ax.spines.values():
    spine.set_color("white")

plt.tight_layout()
plt.show(block=False)

# ==========================
# LOOP PRINCIPAL
# ==========================

def main():
    print("🚗 Corredor X | Telemetria ativa")
    acc = ACCSharedMemory()
    init_csv()

    start = time.time()

    try:
        while True:
            t = round(time.time() - start, 3)
            data = acc.read()

            gas_buf.append(data["gas"])
            brake_buf.append(data["brake"])

            x = np.arange(len(gas_buf))
            line_gas.set_data(x, gas_buf)
            line_brake.set_data(x, brake_buf)

            fig.canvas.draw_idle()
            fig.canvas.flush_events()

            save_row(t, data)
            time.sleep(0.03)

    except KeyboardInterrupt:
        print("\n🛑 Sessão finalizada")
        generate_pdf()

# ==========================
# PDF PÓS-SESSÃO
# ==========================

def generate_pdf():
    print("📄 Gerando PDF da sessão...")
    try:
        print(f"📂 Lendo dados do arquivo CSV: {CSV_FILE}")
        data = np.genfromtxt(CSV_FILE, delimiter=",", skip_header=1)

        if data.size == 0:
            raise ValueError("O arquivo CSV está vazio ou não contém dados válidos.")

        time_axis = data[:, 0]

        plots = [
            ("RPM", data[:, 3]),
            ("Marcha", data[:, 4]),
            ("Ângulo do Volante", data[:, 5]),
            ("Acelerador", data[:, 1]),
            ("Freio", data[:, 2]),
            ("Velocidade", data[:, 6]),
        ]

        print("📊 Gerando gráficos para o PDF...")
        with PdfPages(PDF_FILE) as pdf:
            for title, series in plots:
                fig, ax = plt.subplots()
                ax.plot(time_axis, series)
                ax.set_title(title)
                ax.set_xlabel("Tempo (s)")
                ax.set_ylabel(title)
                ax.grid(True)
                pdf.savefig(fig)
                plt.close(fig)

        print(f"✅ PDF gerado com sucesso: {PDF_FILE}")
    except Exception as e:
        print(f"❌ Erro ao gerar o PDF: {e}")

# ==========================
# ENTRY POINT
# ==========================

if __name__ == "__main__":
    main()

