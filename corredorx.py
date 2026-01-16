#só podemos mudar nosssos caminhos, quando mudamos nossas decisões"
"""
Projeto Corredor X - Telemetria ACC
Versão 2.0 com Offsets Oficiais

Realtime:
- Acelerador & Freio (gráfico ao vivo)

Captura (28 campos):
- Voltas: número, tempo, melhor tempo, delta, posição
- Inputs: gas, brake, steer, gear
- Motor: RPM, combustível
- Pneus: pressão [4], temperatura [4]
- Assistências: TC, ABS
- Condições: temperatura ar/pista, chuva
- Bandeiras: None/Blue/Yellow/Checkered/etc
- Status: in_pit

Export:
- CSV completo (dados/)
- PDF com 11 gráficos (relatorios/)
  * Tempos de volta
  * RPM, marcha, volante
  * Acelerador, freio, velocidade
  * Combustível
  * Temperaturas ar/pista
  * Pressão dos pneus (4 rodas)
  * Temperatura dos pneus (4 rodas)
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
# Baseado em: ACCSharedMemory.h oficial
# ==========================

PHYSICS = {
    "packet_id": 0,
    "gas": 4,
    "brake": 8,
    "fuel": 12,
    "gear": 16,
    "rpm": 20,
    "steer": 24,
    "speed": 28,
    # Arrays de pneus [FL, FR, RL, RR]
    "wheel_slip": 32,        # float[4]
    "tyre_pressure": 48,     # float[4]
    "tyre_core_temp": 80,    # float[4]
    # Assistências (int: 0/1)
    "tc": 112,
    "abs": 116,
    "pit_limiter": 120,
}

GRAPHICS = {
    "packet_id": 0,
    "status": 4,              # 0=OFF, 1=REPLAY, 2=LIVE
    "session": 8,             # 0=Practice, 1=Qualify, 2=Race
    "completed_laps": 268,
    "position": 272,
    "i_current_time": 276,    # ms
    "i_last_time": 280,       # ms
    "i_best_time": 284,       # ms
    "session_time_left": 288, # float ms
    "distance_traveled": 292, # float meters
    "is_in_pit": 296,
    "current_sector": 300,
    "last_sector_time": 304,
    "number_of_laps": 308,
    "flag": 1356,             # 0=None, 1=Blue, 2=Yellow, 5=Checkered
    # Condições climáticas (SIM, estão no Graphics!)
    "air_temp": 1384,         # float °C
    "road_temp": 1388,        # float °C
    "rain_intensity": 1392,   # float 0-1
}

STATIC = {
    "car_model": 68,      # wchar[33]
    "track": 134,         # wchar[33]
    "player_name": 200,   # wchar[33]
    "player_surname": 266,# wchar[33]
    "max_rpm": 410,       # int
    "max_fuel": 414,      # float
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

    def read_wstring(self, offset, size=33):
        self.mm.seek(offset)
        raw = self.mm.read(size * 2)
        return raw.decode("utf-16", errors='ignore').split("\x00")[0]
    
    def read_float_array(self, offset, count=4):
        """Lê array de floats (ex: pneus)"""
        self.mm.seek(offset)
        return struct.unpack(f"{count}f", self.mm.read(4 * count))

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
            "position",
            "lap_time",
            "best_time",
            "delta",
            "gas",
            "brake",
            "rpm",
            "speed",
            "gear",
            "steer",
            "fuel",
            "tc_on",
            "abs_on",
            "tyre_press_fl",
            "tyre_press_fr",
            "tyre_press_rl",
            "tyre_press_rr",
            "tyre_temp_fl",
            "tyre_temp_fr",
            "tyre_temp_rl",
            "tyre_temp_rr",
            "air_temp",
            "road_temp",
            "rain",
            "flag",
            "in_pit",
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
            fuel = physics.read_float(PHYSICS["fuel"])
            rpm = physics.read_int(PHYSICS["rpm"])
            speed = physics.read_float(PHYSICS["speed"])
            gear = physics.read_int(PHYSICS["gear"])
            steer = physics.read_float(PHYSICS["steer"])
            tc_on = physics.read_int(PHYSICS["tc"])
            abs_on = physics.read_int(PHYSICS["abs"])
            
            # Arrays de pneus
            tyre_press = physics.read_float_array(PHYSICS["tyre_pressure"], 4)
            tyre_temp = physics.read_float_array(PHYSICS["tyre_core_temp"], 4)

            # Graphics data
            lap = graphics.read_int(GRAPHICS["completed_laps"])
            position = graphics.read_int(GRAPHICS["position"])
            i_last_time = graphics.read_int(GRAPHICS["i_last_time"]) / 1000.0
            i_best_time = graphics.read_int(GRAPHICS["i_best_time"]) / 1000.0
            delta = i_last_time - i_best_time if i_best_time > 0 else 0.0
            air_temp = graphics.read_float(GRAPHICS["air_temp"])
            road_temp = graphics.read_float(GRAPHICS["road_temp"])
            rain = graphics.read_float(GRAPHICS["rain_intensity"])
            flag = graphics.read_int(GRAPHICS["flag"])
            in_pit = graphics.read_int(GRAPHICS["is_in_pit"])
            
            # Traduzir flag
            flag_names = {0: "None", 1: "Blue", 2: "Yellow", 3: "Black", 
                         4: "White", 5: "Checkered", 6: "Penalty"}
            flag_name = flag_names.get(flag, f"Unknown({flag})")

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
                minutes = int(i_last_time // 60)
                seconds = i_last_time % 60
                delta_sign = "+" if delta > 0 else ""
                print(f"\n🏁 Volta {last_lap} completa")
                print(f"   ⏱️  Tempo: {minutes}:{seconds:06.3f}")
                if i_best_time > 0:
                    print(f"   🏆 Delta: {delta_sign}{delta:.3f}s")
                print(f"   📢 Posição: P{position}")
                last_lap = lap
            elif lap != last_lap:
                last_lap = lap
                print(f"\n🔄 Iniciando Volta {lap} | P{position}")

            # Save data
            save_row([
                t, lap, position, i_last_time, i_best_time, delta,
                gas, brake, rpm, speed, gear, steer, fuel,
                tc_on, abs_on,
                tyre_press[0], tyre_press[1], tyre_press[2], tyre_press[3],
                tyre_temp[0], tyre_temp[1], tyre_temp[2], tyre_temp[3],
                air_temp, road_temp, rain,
                flag_name, in_pit
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

    # Estrutura do CSV: 
    # [0]=time, [1]=lap, [2]=position, [3]=lap_time, [4]=best_time, [5]=delta,
    # [6]=gas, [7]=brake, [8]=rpm, [9]=speed, [10]=gear, [11]=steer, [12]=fuel,
    # [13]=tc_on, [14]=abs_on,
    # [15]=tyre_press_fl, [16]=fr, [17]=rl, [18]=rr,
    # [19]=tyre_temp_fl, [20]=fr, [21]=rl, [22]=rr,
    # [23]=air_temp, [24]=road_temp, [25]=rain, [26]=flag, [27]=in_pit
    
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
                    lap_times_in_lap = data[mask, 3]  # [3] = lap_time
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
            ("🔄 RPM", data[:, 8]),
            ("⚙️ Marcha", data[:, 10]),
            ("🎮 Ângulo do Volante", data[:, 11]),
            ("🚗 Acelerador", data[:, 6]),
            ("🛑 Freio", data[:, 7]),
            ("💨 Velocidade (km/h)", data[:, 9]),
            ("⛽ Combustível (L)", data[:, 12]),
            ("🌡️ Temperatura do Ar (°C)", data[:, 23]),
            ("🛣️ Temperatura da Pista (°C)", data[:, 24]),
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
        
        # Gráfico de pressão dos pneus (todas as 4 rodas)
        fig_press, ax = plt.subplots(figsize=(12, 5))
        ax.plot(time_axis, data[:, 15], label='FL', linewidth=1.5, color='red')
        ax.plot(time_axis, data[:, 16], label='FR', linewidth=1.5, color='orange')
        ax.plot(time_axis, data[:, 17], label='RL', linewidth=1.5, color='blue')
        ax.plot(time_axis, data[:, 18], label='RR', linewidth=1.5, color='cyan')
        ax.set_title('🔧 Pressão dos Pneus (PSI)', fontsize=14, fontweight='bold')
        ax.set_xlabel("Tempo (s)", fontsize=11)
        ax.set_ylabel("PSI", fontsize=11)
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        pdf.savefig(fig_press)
        plt.close(fig_press)
        
        # Gráfico de temperatura dos pneus
        fig_temp, ax = plt.subplots(figsize=(12, 5))
        ax.plot(time_axis, data[:, 19], label='FL', linewidth=1.5, color='red')
        ax.plot(time_axis, data[:, 20], label='FR', linewidth=1.5, color='orange')
        ax.plot(time_axis, data[:, 21], label='RL', linewidth=1.5, color='blue')
        ax.plot(time_axis, data[:, 22], label='RR', linewidth=1.5, color='cyan')
        ax.set_title('🌡️ Temperatura dos Pneus (°C)', fontsize=14, fontweight='bold')
        ax.set_xlabel("Tempo (s)", fontsize=11)
        ax.set_ylabel("°C", fontsize=11)
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        pdf.savefig(fig_temp)
        plt.close(fig_temp)

    num_laps = len([l for l in unique_laps if l > 0]) if len(unique_laps) > 1 else 0
    print(f"✅ PDF gerado com {num_laps} volta(s): {PDF_FILE}")

# ==========================
# ENTRY POINT
# ==========================

if __name__ == "__main__":
    main()
