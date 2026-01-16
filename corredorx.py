#só podemos mudar nosssos caminhos, quando mudamos nossas decisões"
"""
Projeto Corredor X
Telemetria ACC via Shared Memory (Physics)

Realtime:
- Acelerador
- Freio
- Janela não intrusiva

Offline (automático ao encerrar):
- PDF com gráficos separados:
  RPM, Marcha, Ângulo de Volante,
  Acelerador, Freio, Velocidade
"""

# ==========================
# IMPORTS
# ==========================

import mmap
import struct
import time
import csv
import numpy as np
from collections import deque
from datetime import datetime

# matplotlib (dois contextos: realtime e export)
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt

# ==========================
# SHARED MEMORY (ACC)
# ==========================

SHM_NAME = "Local\\acpmf_physics"
SHM_SIZE = 4096

SHM_STATIC_NAME = "Local\\acpmf_static"
SHM_STATIC_SIZE = 824

OFFSET = {
    "gas": 4,
    "brake": 8,
    "gear": 16,
    "rpm": 20,
    "steer": 24,
    "speed": 28,
    "lap_time": 32,          # Tempo da volta atual
    "last_lap_time": 36,     # Tempo da volta anterior
    "lap_count": 52,         # Número da volta
    "air_temp": 56,          # Temperatura do ar
    "road_temp": 60,         # Temperatura da pista
    "rain_intensity": 64,    # Intensidade da chuva (0-1)
    "road_grip": 68,         # Aderência da pista (0-1)
}

class ACCStaticInfo:
    """Lê informações estáticas da sessão (pista, carro, etc)"""
    def __init__(self):
        try:
            self.mm = mmap.mmap(
                -1, SHM_STATIC_SIZE,
                tagname=SHM_STATIC_NAME,
                access=mmap.ACCESS_READ
            )
        except Exception:
            raise RuntimeError(
                "Não foi possível acessar a Shared Memory Static do ACC.\n"
                "Verifique se o jogo está aberto e em pista."
            )
    
    def read(self):
        self.mm.seek(0)
        data = self.mm.read(SHM_STATIC_SIZE)
        
        # Ler strings (wchar = 2 bytes por char)
        # Track name começa no offset 0
        track_bytes = struct.unpack_from("66s", data, 0)[0]
        track_name = track_bytes.decode('utf-16le', errors='ignore').split('\x00')[0]
        
        # Car model começa no offset 132
        car_bytes = struct.unpack_from("66s", data, 132)[0]
        car_name = car_bytes.decode('utf-16le', errors='ignore').split('\x00')[0]
        
        return {
            "track": track_name,
            "car": car_name
        }

class ACCSharedMemory:
    def __init__(self):
        try:
            self.mm = mmap.mmap(
                -1, SHM_SIZE,
                tagname=SHM_NAME,
                access=mmap.ACCESS_READ
            )
        except Exception:
            raise RuntimeError(
                "Não foi possível acessar a Shared Memory do ACC.\n"
                "Verifique se o jogo está aberto e em pista."
            )

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
            "lap_time": struct.unpack_from("i", data, OFFSET["lap_time"])[0],
            "last_lap_time": struct.unpack_from("i", data, OFFSET["last_lap_time"])[0],
            "lap_count": struct.unpack_from("i", data, OFFSET["lap_count"])[0],
            "air_temp": struct.unpack_from("f", data, OFFSET["air_temp"])[0],
            "road_temp": struct.unpack_from("f", data, OFFSET["road_temp"])[0],
            "rain_intensity": struct.unpack_from("f", data, OFFSET["rain_intensity"])[0],
            "road_grip": struct.unpack_from("f", data, OFFSET["road_grip"])[0],
        }

# ==========================
# SESSÃO / ARQUIVOS
# ==========================

import os

# Criar pastas se não existirem
os.makedirs("dados", exist_ok=True)
os.makedirs("relatorios", exist_ok=True)

SESSION_NAME = datetime.now().strftime("%Y%m%d_%H%M%S")
CSV_FILE = os.path.join("dados", f"telemetry_{SESSION_NAME}.csv")
PDF_FILE = os.path.join("relatorios", f"telemetry_{SESSION_NAME}.pdf")

# Variáveis globais para informações da sessão
SESSION_TRACK = ""
SESSION_CAR = ""

def init_csv():
    with open(CSV_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "time",
            "lap",
            "gas",
            "brake",
            "rpm",
            "gear",
            "steer",
            "speed",
            "lap_time",
            "air_temp",
            "road_temp",
            "rain_intensity",
            "road_grip"
        ])

def save_row(t, d, lap):
    with open(CSV_FILE, "a", newline="") as f:
        csv.writer(f).writerow([
            t,
            lap,
            d["gas"],
            d["brake"],
            d["rpm"],
            d["gear"],
            d["steer"],
            d["speed"],
            d["lap_time"],
            d["air_temp"],
            d["road_temp"],
            d["rain_intensity"],
            d["road_grip"]
        ])

# ==========================
# BUFFERS REALTIME
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

ax.set_ylim(0.0, 1.05)
ax.set_xlim(0, MAX_POINTS)
ax.set_title("Acelerador & Freio", color="white")

line_gas, = ax.plot([], [], color="red", linewidth=2, label="Acelerador")
line_brake, = ax.plot([], [], color="lime", linewidth=2, label="Freio")

ax.tick_params(colors="white")
for spine in ax.spines.values():
    spine.set_color("white")

ax.legend(facecolor="black", edgecolor="white", labelcolor="white")

plt.tight_layout()
plt.show(block=False)

# ==========================
# LOOP PRINCIPAL
# ==========================

def main():
    global SESSION_TRACK, SESSION_CAR
    
    print("🚗 Corredor X | Telemetria ativa")
    print("📊 Detecção automática de voltas: ATIVADA")
    
    # Ler informações estáticas
    try:
        static_info = ACCStaticInfo()
        session_data = static_info.read()
        SESSION_TRACK = session_data['track']
        SESSION_CAR = session_data['car']
        
        print("\n🏁 Informações da Sessão:")
        print(f"   🛣️  Pista: {SESSION_TRACK}")
        print(f"   🏎️  Carro: {SESSION_CAR}")
    except Exception as e:
        print(f"\n⚠️  Não foi possível ler informações da sessão: {e}")
        SESSION_TRACK = "Desconhecida"
        SESSION_CAR = "Desconhecido"
    
    acc = ACCSharedMemory()
    init_csv()

    # Ler condições iniciais
    initial_data = acc.read()
    print("\n🌤️  Condições da Pista:")
    print(f"   🌡️  Temperatura do Ar: {initial_data['air_temp']:.1f}°C")
    print(f"   🛣️  Temperatura da Pista: {initial_data['road_temp']:.1f}°C")
    
    rain = initial_data['rain_intensity']
    if rain > 0.5:
        weather = "☔ Chuva Forte"
    elif rain > 0.2:
        weather = "🌧️  Chuva Leve"
    elif rain > 0:
        weather = "🌦️  Garoa"
    else:
        weather = "☀️  Seco"
    print(f"   {weather}")
    
    grip = initial_data['road_grip']
    if grip >= 0.98:
        grip_status = "🟢 Ótima"
    elif grip >= 0.95:
        grip_status = "🟡 Boa"
    elif grip >= 0.90:
        grip_status = "🟠 Média"
    else:
        grip_status = "🔴 Baixa"
    print(f"   🏎️  Aderência: {grip_status} ({grip*100:.1f}%)")
    print()

    start_time = time.time()
    current_lap = 0
    last_lap_count = 0

    try:
        while True:
            t = round(time.time() - start_time, 3)
            data = acc.read()

            # Detectar mudança de volta
            if data["lap_count"] != last_lap_count:
                if last_lap_count > 0:  # Não conta a primeira leitura
                    lap_time_ms = data["last_lap_time"]
                    lap_time_s = lap_time_ms / 1000.0
                    minutes = int(lap_time_s // 60)
                    seconds = lap_time_s % 60
                    print(f"🏁 Volta {last_lap_count} completa! Tempo: {minutes}:{seconds:06.3f}")
                
                current_lap = data["lap_count"]
                last_lap_count = data["lap_count"]
                print(f"🔄 Iniciando Volta {current_lap}")

            # buffers realtime
            gas_buf.append(data["gas"])
            brake_buf.append(data["brake"])

            x = np.arange(len(gas_buf))
            line_gas.set_data(x, gas_buf)
            line_brake.set_data(x, brake_buf)

            fig.canvas.draw_idle()
            fig.canvas.flush_events()

            # grava telemetria completa
            save_row(t, data, current_lap)

            time.sleep(0.03)  # ~30 Hz

    except KeyboardInterrupt:
        print("\n🛑 Sessão encerrada")

        # FECHA JANELA REALTIME ANTES DO PDF
        plt.ioff()
        plt.close(fig)

        generate_pdf()

# ==========================
# GERAÇÃO DE PDF (HEADLESS)
# ==========================

def generate_pdf():
    print("📄 Gerando PDF da sessão...")

    # backend sem GUI
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages

    data = np.genfromtxt(CSV_FILE, delimiter=",", skip_header=1)

    if data.size == 0:
        print("⚠️ Nenhum dado capturado para gerar PDF")
        return

    time_axis = data[:, 0]
    lap_data = data[:, 1].astype(int)
    
    # Dados organizados: [time, lap, gas, brake, rpm, gear, steer, speed, lap_time, air_temp, road_temp, rain, grip]
    plots = [
        ("RPM", data[:, 4]),
        ("Marcha", data[:, 5]),
        ("Ângulo do Volante", data[:, 6]),
        ("Acelerador", data[:, 2]),
        ("Freio", data[:, 3]),
        ("Velocidade", data[:, 7]),
    ]

    with PdfPages(PDF_FILE) as pdf:
        # Página 1: Informações da Sessão e Condições Climáticas
        fig_info = plt.figure(figsize=(12, 11))
        
        # Título principal
        fig_info.suptitle('🏎️  CORREDOR X - RELATÓRIO DE TELEMETRIA', 
                         fontsize=20, fontweight='bold', y=0.98)
        
        # Informações da sessão (texto no topo)
        info_text = f"""
🏁 INFORMAÇÕES DA SESSÃO

🛣️  Pista: {SESSION_TRACK}
🏎️  Carro: {SESSION_CAR}
📅 Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
⏱️  Duração: {time_axis[-1]:.1f}s ({int(time_axis[-1]//60)}min {int(time_axis[-1]%60)}s)
        """
        
        fig_info.text(0.5, 0.88, info_text, ha='center', va='top',
                     fontsize=12, family='monospace',
                     bbox=dict(boxstyle='round', facecolor='#f0f0f0', alpha=0.8))
        
        # Gráficos climáticos (4 subplots)
        gs = fig_info.add_gridspec(2, 2, left=0.1, right=0.9, top=0.70, bottom=0.08, 
                                   hspace=0.3, wspace=0.3)
        
        ax1 = fig_info.add_subplot(gs[0, 0])
        ax2 = fig_info.add_subplot(gs[0, 1])
        ax3 = fig_info.add_subplot(gs[1, 0])
        ax4 = fig_info.add_subplot(gs[1, 1])
        
        # Temperatura do Ar
        air_temp = data[:, 9]
        ax1.plot(time_axis, air_temp, color='#ff6b6b', linewidth=2)
        ax1.set_title('🌡️  Temperatura do Ar', fontsize=12, fontweight='bold')
        ax1.set_xlabel('Tempo (s)')
        ax1.set_ylabel('Temperatura (°C)')
        ax1.grid(True, alpha=0.3)
        ax1.fill_between(time_axis, air_temp, alpha=0.3, color='#ff6b6b')
        avg_air = np.mean(air_temp)
        ax1.axhline(y=avg_air, color='red', linestyle='--', label=f'Média: {avg_air:.1f}°C')
        ax1.legend()
        
        # Temperatura da Pista
        road_temp = data[:, 10]
        ax2.plot(time_axis, road_temp, color='#ffa500', linewidth=2)
        ax2.set_title('🛣️  Temperatura da Pista', fontsize=12, fontweight='bold')
        ax2.set_xlabel('Tempo (s)')
        ax2.set_ylabel('Temperatura (°C)')
        ax2.grid(True, alpha=0.3)
        ax2.fill_between(time_axis, road_temp, alpha=0.3, color='#ffa500')
        avg_road = np.mean(road_temp)
        ax2.axhline(y=avg_road, color='darkorange', linestyle='--', label=f'Média: {avg_road:.1f}°C')
        ax2.legend()
        
        # Intensidade da Chuva
        rain_intensity = data[:, 11]
        ax3.plot(time_axis, rain_intensity * 100, color='#4a90e2', linewidth=2)
        ax3.set_title('☔ Intensidade da Chuva', fontsize=12, fontweight='bold')
        ax3.set_xlabel('Tempo (s)')
        ax3.set_ylabel('Intensidade (%)')
        ax3.grid(True, alpha=0.3)
        ax3.fill_between(time_axis, rain_intensity * 100, alpha=0.3, color='#4a90e2')
        ax3.set_ylim([0, 105])
        
        # Aderência da Pista
        road_grip = data[:, 12]
        ax4.plot(time_axis, road_grip * 100, color='#2ecc71', linewidth=2)
        ax4.set_title('🏎️  Aderência da Pista', fontsize=12, fontweight='bold')
        ax4.set_xlabel('Tempo (s)')
        ax4.set_ylabel('Grip (%)')
        ax4.grid(True, alpha=0.3)
        ax4.fill_between(time_axis, road_grip * 100, alpha=0.3, color='#2ecc71')
        ax4.set_ylim([85, 100])
        avg_grip = np.mean(road_grip)
        ax4.axhline(y=avg_grip * 100, color='darkgreen', linestyle='--', label=f'Média: {avg_grip*100:.1f}%')
        ax4.legend()
        
        plt.tight_layout()
        pdf.savefig(fig_info)
        plt.close(fig_info)

        # Página 2: Resumo de Voltas
        unique_laps = np.unique(lap_data)
        if len(unique_laps) > 1:
            fig_summary, ax = plt.subplots(figsize=(10, 6))
            
            lap_times = []
            lap_numbers = []
            
            for lap in unique_laps:
                if lap > 0:
                    lap_mask = lap_data == lap
                    lap_times_ms = data[lap_mask, 8]
                    if len(lap_times_ms) > 0:
                        # Pegar o último valor (tempo final da volta)
                        final_time = lap_times_ms[-1] / 1000.0
                        if final_time > 0:  # Volta completa
                            lap_numbers.append(int(lap))
                            lap_times.append(final_time)
            
            if lap_times:
                ax.bar(lap_numbers, lap_times, color='#00aa00', alpha=0.7, edgecolor='black')
                ax.set_title('Tempos de Volta', fontsize=16, fontweight='bold')
                ax.set_xlabel('Número da Volta', fontsize=12)
                ax.set_ylabel('Tempo (s)', fontsize=12)
                ax.grid(True, alpha=0.3)
                
                # Adicionar valores nas barras
                for i, (lap_num, lap_time) in enumerate(zip(lap_numbers, lap_times)):
                    minutes = int(lap_time // 60)
                    seconds = lap_time % 60
                    ax.text(lap_num, lap_time, f"{minutes}:{seconds:06.3f}", 
                           ha='center', va='bottom', fontsize=9, fontweight='bold')
                
                # Melhor volta
                best_lap_idx = np.argmin(lap_times)
                best_lap_num = lap_numbers[best_lap_idx]
                best_time = lap_times[best_lap_idx]
                minutes = int(best_time // 60)
                seconds = best_time % 60
                
                ax.axhline(y=best_time, color='red', linestyle='--', linewidth=2, 
                          label=f'Melhor: Volta {best_lap_num} ({minutes}:{seconds:06.3f})')
                ax.legend(fontsize=11)
            
            plt.tight_layout()
            pdf.savefig(fig_summary)
            plt.close(fig_summary)

        # Páginas seguintes: Gráficos com cores por volta
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
                  '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
        
        for title, series in plots:
            fig_p, ax = plt.subplots(figsize=(12, 5))
            
            # Plotar cada volta com cor diferente
            for i, lap in enumerate(unique_laps):
                if lap > 0:
                    lap_mask = lap_data == lap
                    color = colors[i % len(colors)]
                    ax.plot(time_axis[lap_mask], series[lap_mask], 
                           label=f'Volta {int(lap)}', color=color, linewidth=1.5, alpha=0.8)
            
            ax.set_title(title, fontsize=14, fontweight='bold')
            ax.set_xlabel("Tempo (s)", fontsize=11)
            ax.set_ylabel(title, fontsize=11)
            ax.grid(True, alpha=0.3)
            
            if len(unique_laps) > 1:
                ax.legend(loc='best', fontsize=9)
            
            plt.tight_layout()
            pdf.savefig(fig_p)
            plt.close(fig_p)

    num_laps = len(unique_laps) - 1 if 0 in unique_laps else len(unique_laps)
    print(f"✅ PDF gerado com {num_laps} volta(s): {PDF_FILE}")

# ==========================
# ENTRY POINT
# ==========================

if __name__ == "__main__":
    main()
