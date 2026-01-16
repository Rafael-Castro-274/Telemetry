#só podemos mudar nosssos caminhos, quando mudamos nossas decisões"
"""
Projeto Corredor X
Telemetria ACC via Shared Memory

Realtime:
- Acelerador
- Freio

Gravação:
- Voltas automáticas
- Tempo de volta
- Temperatura pista / ar
- ABS ativo
- Composto do pneu

Export:
- CSV + PDF pós-sessão
"""

# ==========================
# IMPORTS
# ==========================

import mmap
import struct
import time
import csv
import os
import numpy as np
from collections import deque
from datetime import datetime

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt

# ==========================
# SHARED MEMORY NAMES
# ==========================

SHM_PHYSICS  = "Local\\acpmf_physics"
SHM_GRAPHICS = "Local\\acpmf_graphics"
SHM_STATIC   = "Local\\acpmf_static"

SHM_SIZE = 4096

# ==========================
# OFFSETS (ACC)
# ==========================

PHYSICS = {
    "gas": 4,
    "brake": 8,
    "abs": 44,
    "rpm": 20,
    "speed": 28,
    "steer": 24,
    "gear": 16,
}

GRAPHICS = {
    "completed_laps": 32,
    "last_lap_ms": 36,
}

STATIC = {
    "air_temp": 8,
    "road_temp": 12,
    "tyre_compound": 40,  # wchar[50]
}

# ==========================
# SHARED MEMORY HANDLER
# ==========================

class ACCSharedMemory:
    def __init__(self, name):
        try:
            self.mm = mmap.mmap(-1, SHM_SIZE, tagname=name, access=mmap.ACCESS_READ)
        except Exception as e:
            raise RuntimeError(
                f"Não foi possível acessar {name}.\n"
                f"Verifique se o ACC está aberto e em pista.\n"
                f"Erro: {e}"
            )

    def read_float(self, offset):
        self.mm.seek(offset)
        return struct.unpack("f", self.mm.read(4))[0]

    def read_int(self, offset):
        self.mm.seek(offset)
        return struct.unpack("i", self.mm.read(4))[0]

    def read_wstring(self, offset, size=50):
        self.mm.seek(offset)
        raw = self.mm.read(size * 2)
        return raw.decode("utf-16", errors='ignore').split("\x00")[0]

# ==========================
# SESSION FILES
# ==========================

# Criar pastas se não existirem
os.makedirs("dados", exist_ok=True)
os.makedirs("relatorios", exist_ok=True)

SESSION_ID = datetime.now().strftime("%Y%m%d_%H%M%S")
CSV_FILE = os.path.join("dados", f"telemetry_{SESSION_ID}.csv")
PDF_FILE = os.path.join("relatorios", f"telemetry_{SESSION_ID}.pdf")

def init_csv():
    with open(CSV_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "time",
            "lap",
            "lap_time",
            "gas",
            "brake",
            "rpm",
            "speed",
            "gear",
            "steer",
            "abs_on",
            "air_temp",
            "road_temp",
            "tyre_compound",
        ])

def save_row(row):
    with open(CSV_FILE, "a", newline="") as f:
        csv.writer(f).writerow(row)

# ==========================
# REALTIME PLOT
# ==========================

plt.ion()
fig, ax = plt.subplots(figsize=(6, 3))
fig.canvas.manager.set_window_title("Corredor X | Realtime")

fig.patch.set_facecolor("black")
ax.set_facecolor("black")

ax.set_ylim(0, 1.05)
ax.set_xlim(0, 300)
ax.set_title("Acelerador & Freio", color="white")

line_gas, = ax.plot([], [], color="red", linewidth=2, label="Acelerador")
line_brake, = ax.plot([], [], color="lime", linewidth=2, label="Freio")

ax.tick_params(colors="white")
for spine in ax.spines.values():
    spine.set_color("white")

ax.legend(facecolor="black", edgecolor="white", labelcolor="white")
plt.tight_layout()
plt.show(block=False)

gas_buf = deque(maxlen=300)
brake_buf = deque(maxlen=300)


# ==========================
# MAIN LOOP
# ==========================

def main():
    print("🚗 Corredor X | Telemetria ativa")
    print("📊 Conectando às Shared Memories do ACC...")
    
    try:
        physics  = ACCSharedMemory(SHM_PHYSICS)
        graphics = ACCSharedMemory(SHM_GRAPHICS)
        static   = ACCSharedMemory(SHM_STATIC)
    except RuntimeError as e:
        print(f"\n❌ Erro: {e}")
        return

    init_csv()

    start_time = time.time()
    last_lap = 0

    print("✅ Conectado! Capturando telemetria...")
    print()

    try:
        while True:
            t = round(time.time() - start_time, 3)

            # Physics data
            gas = physics.read_float(PHYSICS["gas"])
            brake = physics.read_float(PHYSICS["brake"])
            rpm = physics.read_int(PHYSICS["rpm"])
            speed = physics.read_float(PHYSICS["speed"])
            gear = physics.read_int(PHYSICS["gear"])
            steer = physics.read_float(PHYSICS["steer"])
            abs_on = physics.read_float(PHYSICS["abs"]) > 0.0

            # Graphics data
            lap = graphics.read_int(GRAPHICS["completed_laps"])
            lap_time = graphics.read_int(GRAPHICS["last_lap_ms"]) / 1000.0

            # Static data
            air_temp = static.read_float(STATIC["air_temp"])
            road_temp = static.read_float(STATIC["road_temp"])
            compound = static.read_wstring(STATIC["tyre_compound"])

            # Realtime plot
            gas_buf.append(gas)
            brake_buf.append(brake)
            x = np.arange(len(gas_buf))
            line_gas.set_data(x, gas_buf)
            line_brake.set_data(x, brake_buf)
            fig.canvas.draw_idle()
            fig.canvas.flush_events()

            # Lap detection
            if lap != last_lap and last_lap > 0:
                minutes = int(lap_time // 60)
                seconds = lap_time % 60
                print(f"🏁 Volta {last_lap} completa | Tempo: {minutes}:{seconds:06.3f}")
                last_lap = lap
            elif lap != last_lap:
                last_lap = lap
                print(f"🔄 Iniciando Volta {lap}")

            # Save data
            save_row([
                t, lap, lap_time,
                gas, brake, rpm, speed, gear, steer,
                abs_on, air_temp, road_temp,
                compound
            ])

            time.sleep(0.03)

    except KeyboardInterrupt:
        print("\n🛑 Sessão encerrada")
        
        # Fechar janela realtime
        plt.ioff()
        plt.close(fig)
        
        # Gerar PDF
        generate_pdf()

# ==========================
# PDF GENERATION
# ==========================

def generate_pdf():
    print("📄 Gerando PDF da sessão...")

    # Backend sem GUI
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages

    try:
        data = np.genfromtxt(CSV_FILE, delimiter=",", skip_header=1, encoding='utf-8')
    except:
        data = np.genfromtxt(CSV_FILE, delimiter=",", skip_header=1)

    if data.size == 0:
        print("⚠️ Nenhum dado capturado para gerar PDF")
        return

    # Dados organizados: [time, lap, lap_time, gas, brake, rpm, speed, gear, steer, abs_on, air_temp, road_temp, compound]
    time_axis = data[:, 0]
    lap_data = data[:, 1].astype(int)

    with PdfPages(PDF_FILE) as pdf:
        # Página 1: Resumo de Voltas
        unique_laps = np.unique(lap_data)
        if len(unique_laps) > 1:
            fig_laps, ax = plt.subplots(figsize=(10, 6))
            
            lap_times = []
            lap_numbers = []
            
            for lap_num in unique_laps:
                if lap_num > 0:
                    mask = lap_data == lap_num
                    lap_times_in_lap = data[mask, 2]
                    if len(lap_times_in_lap) > 0:
                        final_time = lap_times_in_lap[-1]
                        if final_time > 0:
                            lap_numbers.append(int(lap_num))
                            lap_times.append(final_time)
            
            if lap_times:
                ax.bar(lap_numbers, lap_times, color='#00aa00', alpha=0.7, edgecolor='black')
                ax.set_title('⏱️ Tempos de Volta', fontsize=16, fontweight='bold')
                ax.set_xlabel('Número da Volta', fontsize=12)
                ax.set_ylabel('Tempo (s)', fontsize=12)
                ax.grid(True, alpha=0.3)
                
                # Valores nas barras
                for lap_num, lap_time in zip(lap_numbers, lap_times):
                    minutes = int(lap_time // 60)
                    seconds = lap_time % 60
                    ax.text(lap_num, lap_time, f"{minutes}:{seconds:06.3f}", 
                           ha='center', va='bottom', fontsize=9, fontweight='bold')
                
                # Melhor volta
                best_idx = np.argmin(lap_times)
                best_lap = lap_numbers[best_idx]
                best_time = lap_times[best_idx]
                minutes = int(best_time // 60)
                seconds = best_time % 60
                ax.axhline(y=best_time, color='red', linestyle='--', linewidth=2,
                          label=f'Melhor: Volta {best_lap} ({minutes}:{seconds:06.3f})')
                ax.legend(fontsize=11)
            
            plt.tight_layout()
            pdf.savefig(fig_laps)
            plt.close(fig_laps)

        # Páginas seguintes: Gráficos de telemetria
        plots = [
            ("🔄 RPM", data[:, 5]),
            ("⚙️ Marcha", data[:, 7]),
            ("🎮 Ângulo do Volante", data[:, 8]),
            ("🚗 Acelerador", data[:, 3]),
            ("🛑 Freio", data[:, 4]),
            ("💨 Velocidade", data[:, 6]),
            ("🌡️ Temperatura do Ar", data[:, 10]),
            ("🛣️ Temperatura da Pista", data[:, 11]),
        ]

        for title, series in plots:
            fig_p, ax = plt.subplots(figsize=(12, 5))
            ax.plot(time_axis, series, linewidth=1.5, color='#0066cc')
            ax.set_title(title, fontsize=14, fontweight='bold')
            ax.set_xlabel("Tempo (s)", fontsize=11)
            ax.set_ylabel(title.split(' ', 1)[1] if ' ' in title else title, fontsize=11)
            ax.grid(True, alpha=0.3)
            plt.tight_layout()
            pdf.savefig(fig_p)
            plt.close(fig_p)

    num_laps = len([l for l in unique_laps if l > 0]) if len(unique_laps) > 1 else 0
    print(f"✅ PDF gerado com {num_laps} volta(s): {PDF_FILE}")

# ==========================
# ENTRY POINT
# ==========================

if __name__ == "__main__":
    main()
