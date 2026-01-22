import tkinter as tk
from tkinter import messagebox
import ctypes
import threading
import time
from dataclasses import dataclass

# ======================================================
# 1. CONFIGURAÇÕES E CONSTANTES
# ======================================================
GEAR_MAP = {
    0: "R", 1: "N", 2: "1", 3: "2", 4: "3", 
    5: "4", 6: "5", 7: "6", 8: "7", 9: "8"
}
FILE_MAP_READ = 0x0004
MAX_RPM_GT3 = 9000  # Referência para a barra de RPM

# ======================================================
# 2. ESTRUTURAS DE MEMÓRIA (C++ / ACC)
# ======================================================
class SPageFilePhysics(ctypes.Structure):
    _pack_ = 4
    _fields_ = [
        ("packetId", ctypes.c_int),
        ("gas", ctypes.c_float),
        ("brake", ctypes.c_float),
        ("fuel", ctypes.c_float),
        ("gear", ctypes.c_int),
        ("rpm", ctypes.c_int),
        ("steerAngle", ctypes.c_float),
        ("speedKmh", ctypes.c_float),
        ("velocity", ctypes.c_float * 3),
        ("accG", ctypes.c_float * 3),
        ("wheelSlip", ctypes.c_float * 4),
        ("wheelLoad", ctypes.c_float * 4),
        ("wheelPressure", ctypes.c_float * 4), # <-- Pressão aqui
        ("wheelAngularSpeed", ctypes.c_float * 4),
        ("tyreWear", ctypes.c_float * 4),
        ("tyreDirtyLevel", ctypes.c_float * 4),
        ("tyreCoreTemp", ctypes.c_float * 4),
        ("camberRAD", ctypes.c_float * 4),
        ("suspensionTravel", ctypes.c_float * 4),
        ("drs", ctypes.c_float),
        ("tc", ctypes.c_float),
        ("heading", ctypes.c_float),
        ("pitch", ctypes.c_float),
        ("roll", ctypes.c_float),
        ("cgHeight", ctypes.c_float),
        ("carDamage", ctypes.c_float * 5),
        ("numberOfTyresOut", ctypes.c_int),
        ("pitLimiterOn", ctypes.c_int),
        ("abs", ctypes.c_float),
        ("kersCharge", ctypes.c_float),
        ("kersInput", ctypes.c_float),
        ("isStationary", ctypes.c_int),
        ("suspensionTravelNormalized", ctypes.c_float * 4),
        ("waterTemp", ctypes.c_float),
        ("oilTemp", ctypes.c_float),
        ("fuelInTank", ctypes.c_float),
        ("tyreTemp", ctypes.c_float * 4),
        ("padLife", ctypes.c_float * 4),
        ("discLife", ctypes.c_float * 4),
        ("ignitionOn", ctypes.c_int),
        ("starterEngineOn", ctypes.c_int),
        ("isEngineRunning", ctypes.c_int),
        ("kerbVibration", ctypes.c_float),
        ("slipVibrations", ctypes.c_float),
        ("gVibrations", ctypes.c_float),
        ("absVibrations", ctypes.c_float),
        ("kerbShift", ctypes.c_float), 
        ("gap1", ctypes.c_byte * 4), 
        ("brakeBias", ctypes.c_float),
    ]

class Graphics(ctypes.Structure):
    _pack_ = 4
    _fields_ = [
        ("packetId", ctypes.c_int),
        ("status", ctypes.c_int),
        ("session", ctypes.c_int),
        ("currentTime", ctypes.c_wchar * 15),
        ("lastTime", ctypes.c_wchar * 15),
        ("bestTime", ctypes.c_wchar * 15),
        ("split", ctypes.c_wchar * 15),
        ("completedLaps", ctypes.c_int),
        ("position", ctypes.c_int),
        ("iCurrentTime", ctypes.c_int),
        ("iLastTime", ctypes.c_int),
        ("iBestTime", ctypes.c_int),
        ("sessionTimeLeft", ctypes.c_float),
        ("distanceTraveled", ctypes.c_float),
        ("isInPit", ctypes.c_int),
        ("currentSectorIndex", ctypes.c_int),
        ("lastSectorTime", ctypes.c_int),
        ("numberOfLaps", ctypes.c_int),
        ("tyreCompound", ctypes.c_wchar * 33),
        ("replayTimeMultiplier", ctypes.c_float),
        ("normalizedCarPosition", ctypes.c_float),
        ("activeCars", ctypes.c_int),
        ("carCoordinates", (ctypes.c_float * 3) * 60),
        ("carID", ctypes.c_int * 60),
        ("playerCarID", ctypes.c_int),
        ("penaltyTime", ctypes.c_float),
        ("flag", ctypes.c_int),
        ("penalty", ctypes.c_int),
        ("idealLineOn", ctypes.c_int),
        ("isInPitLane", ctypes.c_int),
        ("surfaceGrip", ctypes.c_float),
        ("mandatoryPitDone", ctypes.c_int),
        ("windSpeed", ctypes.c_float),
        ("windDirection", ctypes.c_float),
        ("isSetupMenuVisible", ctypes.c_int),
        ("mainDisplayIndex", ctypes.c_int),
        ("secondaryDisplayIndex", ctypes.c_int),
        ("TC", ctypes.c_int),
        ("TCCut", ctypes.c_int),
        ("EngineMap", ctypes.c_int), 
        ("ABS", ctypes.c_int),
    ]

# ======================================================
# 3. ESTADO DA TELEMETRIA
# ======================================================
@dataclass
class TelemetryData:
    status: str = "Aguardando ACC..."
    gear: str = "N"
    speed: int = 0
    rpm: int = 0
    gas: float = 0.0
    brake: float = 0.0
    fuel: float = 0.0
    brake_bias: float = 0.0
    
    # Eletrônica
    tc1: int = 0
    tc2: int = 0
    abs_val: int = 0
    engine_map: int = 0
    
    # Pneus
    tyre_core_temp: list = None 
    tyre_pressure: list = None # Adicionado lista de pressões
    connected: bool = False

# ======================================================
# 4. LEITOR DE MEMÓRIA (BACKEND)
# ======================================================
class ACCReader:
    def __init__(self, data_store):
        self.data = data_store
        self.running = False
        self.thread = None
        self.kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        self.kernel32.OpenFileMappingW.restype = ctypes.c_void_p
        self.kernel32.MapViewOfFile.restype = ctypes.c_void_p
        self.kernel32.UnmapViewOfFile.argtypes = [ctypes.c_void_p]
        self.kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
        
    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)

    def _loop(self):
        h_phys = None
        h_graph = None

        while self.running:
            try:
                if not h_phys or not h_graph:
                    h_phys = self.kernel32.OpenFileMappingW(FILE_MAP_READ, False, "Local\\acpmf_physics")
                    h_graph = self.kernel32.OpenFileMappingW(FILE_MAP_READ, False, "Local\\acpmf_graphics")
                    
                    if h_phys and h_graph:
                        self.data.status = "CONECTADO"
                        self.data.connected = True
                    else:
                        self.data.status = "AGUARDANDO SIMULADOR..."
                        self.data.connected = False
                        time.sleep(1)
                        continue

                # --- LEITURA PHYSICS ---
                v_phys = self.kernel32.MapViewOfFile(h_phys, FILE_MAP_READ, 0, 0, ctypes.sizeof(SPageFilePhysics))
                if v_phys:
                    p = SPageFilePhysics.from_address(v_phys)
                    
                    self.data.gear = GEAR_MAP.get(p.gear, "?")
                    self.data.rpm = p.rpm
                    self.data.speed = int(p.speedKmh)
                    self.data.gas = p.gas
                    self.data.brake = p.brake
                    self.data.fuel = p.fuel
                    self.data.brake_bias = p.brakeBias
                    
                    # Leitura de Pneus (Temp + Pressão)
                    self.data.tyre_core_temp = [p.tyreCoreTemp[0], p.tyreCoreTemp[1], p.tyreCoreTemp[2], p.tyreCoreTemp[3]]
                    self.data.tyre_pressure = [p.wheelPressure[0], p.wheelPressure[1], p.wheelPressure[2], p.wheelPressure[3]]
                    
                    self.kernel32.UnmapViewOfFile(v_phys)

                # --- LEITURA GRAPHICS ---
                v_graph = self.kernel32.MapViewOfFile(h_graph, FILE_MAP_READ, 0, 0, ctypes.sizeof(Graphics))
                if v_graph:
                    g = Graphics.from_address(v_graph)
                    self.data.tc1 = g.TC
                    self.data.tc2 = g.TCCut
                    self.data.abs_val = g.ABS
                    self.data.engine_map = g.EngineMap + 1
                    self.kernel32.UnmapViewOfFile(v_graph)

            except Exception as e:
                print(f"Erro: {e}")
                self.data.status = "ERRO LEITURA"
                if h_phys: self.kernel32.CloseHandle(h_phys)
                if h_graph: self.kernel32.CloseHandle(h_graph)
                h_phys, h_graph = None, None
            
            time.sleep(0.016)

# ======================================================
# 5. INTERFACE GRÁFICA (FRONTEND)
# ======================================================
class DashboardApp(tk.Tk):
    def __init__(self, data_store):
        super().__init__()
        self.data = data_store
        
        self.title("ACC Dashboard Pro")
        self.geometry("400x680") # Aumentei um pouco a altura para caber melhor
        self.configure(bg="#121212")
        self.resizable(False, False)

        self._init_ui()
        self._update_loop()

    def _init_ui(self):
        style_bg = "#121212"
        
        self.lbl_status = tk.Label(self, text="...", font=("Segoe UI", 9), bg=style_bg, fg="#888")
        self.lbl_status.pack(pady=5)

        # 1. Gear e Speed
        frame_top = tk.Frame(self, bg=style_bg)
        frame_top.pack(pady=5)
        
        self.lbl_gear = tk.Label(frame_top, text="N", font=("Verdana", 60, "bold"), bg=style_bg, fg="#FFD700")
        self.lbl_gear.grid(row=0, column=0, padx=20)
        
        self.lbl_speed = tk.Label(frame_top, text="0", font=("Verdana", 60, "bold"), bg=style_bg, fg="#00E5FF")
        self.lbl_speed.grid(row=0, column=1, padx=20)

        # 2. RPM e PEDAIS
        frame_inputs = tk.Frame(self, bg="#1E1E1E", bd=1, relief="solid")
        frame_inputs.pack(fill="x", padx=15, pady=5)

        # RPM
        tk.Label(frame_inputs, text="RPM", font=("Segoe UI", 8, "bold"), bg="#1E1E1E", fg="#AAA").pack(anchor="w", padx=5)
        self.cv_rpm = tk.Canvas(frame_inputs, width=350, height=20, bg="#252525", highlightthickness=0)
        self.cv_rpm.pack(pady=(0, 10))

        # Pedais
        frame_pedals = tk.Frame(frame_inputs, bg="#1E1E1E")
        frame_pedals.pack(fill="x", padx=5, pady=5)

        # Gas
        f_gas = tk.Frame(frame_pedals, bg="#1E1E1E")
        f_gas.pack(side="left", expand=True, fill="x")
        tk.Label(f_gas, text="ACEL", font=("Segoe UI", 7), bg="#1E1E1E", fg="#44FF44").pack(anchor="w")
        self.cv_gas = tk.Canvas(f_gas, width=160, height=15, bg="#252525", highlightthickness=0)
        self.cv_gas.pack()

        # Brake
        f_brake = tk.Frame(frame_pedals, bg="#1E1E1E")
        f_brake.pack(side="right", expand=True, fill="x")
        tk.Label(f_brake, text="TRAVÃO", font=("Segoe UI", 7), bg="#1E1E1E", fg="#FF4444").pack(anchor="e")
        self.cv_brake = tk.Canvas(f_brake, width=160, height=15, bg="#252525", highlightthickness=0)
        self.cv_brake.pack()

        # 3. Brake Bias
        frame_bb = tk.Frame(self, bg="#1E1E1E", bd=1, relief="solid")
        frame_bb.pack(fill="x", padx=15, pady=10)
        
        tk.Label(frame_bb, text="BRAKE BIAS", font=("Segoe UI", 8), bg="#1E1E1E", fg="#AAA").pack(pady=(5,0))
        self.lbl_bb_val = tk.Label(frame_bb, text="--.-%", font=("Consolas", 24, "bold"), bg="#1E1E1E", fg="#FF00FF")
        self.lbl_bb_val.pack()

        self.cv_bb = tk.Canvas(frame_bb, width=350, height=10, bg="#252525", highlightthickness=0)
        self.cv_bb.pack(pady=10)

        # 4. Pneus (Agora com Pressão)
        frame_tyres = tk.Frame(self, bg="#121212")
        frame_tyres.pack(pady=5)
        
        self.tyre_temp_labels = [] # Lista para labels de temperatura
        self.tyre_pres_labels = [] # Lista para labels de pressão
        
        pos = [(0,0), (0,1), (1,0), (1,1)]
        # Layout: FL, FR, RL, RR
        for i, (r, c) in enumerate(pos):
            # Aumentei altura de 45 para 55 para caber a pressão
            f = tk.Frame(frame_tyres, bg="#222", width=70, height=55) 
            f.grid(row=r, column=c, padx=5, pady=5)
            f.pack_propagate(False)
            
            # Label Temperatura (Topo)
            l_temp = tk.Label(f, text="--°", font=("Segoe UI", 12, "bold"), bg="#222", fg="white")
            l_temp.pack(pady=(5,0))
            self.tyre_temp_labels.append(l_temp)
            
            # Label Pressão (Baixo) - Fonte menor, cor Ciano
            l_pres = tk.Label(f, text="-- psi", font=("Segoe UI", 9), bg="#222", fg="#00E5FF")
            l_pres.pack()
            self.tyre_pres_labels.append(l_pres)

        # 5. Eletrônica
        frame_elec = tk.Frame(self, bg="#1E1E1E")
        frame_elec.pack(fill="x", padx=15, pady=10)
        self.lbl_tc1 = self._create_elec_box(frame_elec, "TC1", 0)
        self.lbl_tc2 = self._create_elec_box(frame_elec, "TC2", 1)
        self.lbl_abs = self._create_elec_box(frame_elec, "ABS", 2)
        self.lbl_map = self._create_elec_box(frame_elec, "MAP", 3)

    def _create_elec_box(self, parent, title, col):
        f = tk.Frame(parent, bg="#1E1E1E")
        f.grid(row=0, column=col, padx=12, pady=5)
        tk.Label(f, text=title, font=("Segoe UI", 8), bg="#1E1E1E", fg="#AAA").pack()
        l = tk.Label(f, text="-", font=("Consolas", 14, "bold"), bg="#1E1E1E", fg="white")
        l.pack()
        return l

    def _update_loop(self):
        status_color = "#44FF44" if self.data.connected else "#FF4444"
        self.lbl_status.config(text=self.data.status, fg=status_color)

        if self.data.connected:
            self.lbl_gear.config(text=self.data.gear)
            self.lbl_speed.config(text=str(self.data.speed))
            
            # Gráficos
            self._draw_rpm(self.data.rpm)
            self._draw_pedals(self.data.gas, self.data.brake)

            # Electronics
            self.lbl_tc1.config(text=str(self.data.tc1), fg="#44FF44" if self.data.tc1 > 0 else "#555")
            self.lbl_tc2.config(text=str(self.data.tc2), fg="#44FF44" if self.data.tc2 > 0 else "#555")
            self.lbl_abs.config(text=str(self.data.abs_val), fg="#FFAA00" if self.data.abs_val > 0 else "#555")
            self.lbl_map.config(text=str(self.data.engine_map), fg="#00E5FF")

            # Brake Bias
            bb = self.data.brake_bias * 100
            self.lbl_bb_val.config(text=f"{bb:.1f}%")
            self._draw_bb_bar(bb)

            # --- Pneus: Temperatura ---
            if self.data.tyre_core_temp:
                for i, temp in enumerate(self.data.tyre_core_temp):
                    color = "#00FFFF"
                    if temp > 70: color = "#44FF44"
                    if temp > 100: color = "#FF4444"
                    self.tyre_temp_labels[i].config(text=f"{temp:.0f}°", fg=color)
            
            # --- Pneus: Pressão (Novo) ---
            if self.data.tyre_pressure:
                for i, press in enumerate(self.data.tyre_pressure):
                    # ACC entrega PSI nativo na SharedMemory
                    self.tyre_pres_labels[i].config(text=f"{press:.1f} psi")

        self.after(20, self._update_loop)

    def _draw_rpm(self, rpm):
        self.cv_rpm.delete("all")
        width = 350
        pct = min(1.0, rpm / MAX_RPM_GT3)
        w_bar = width * pct
        
        # Cores RPM
        if pct < 0.70:
            color = "#22FF22"
        elif pct < 0.84:
            color = "#FFFF00"
        else:
            color = "#FF2222"
            if pct > 0.98 and int(time.time() * 10) % 2 == 0:
                color = "#FFFFFF"

        self.cv_rpm.create_rectangle(0, 0, w_bar, 20, fill=color, outline="")

        txt = f"{rpm} RPM"
        cx, cy = width / 2, 10
        self.cv_rpm.create_text(cx+1, cy+1, text=txt, fill="black", font=("Segoe UI", 9, "bold"))
        self.cv_rpm.create_text(cx, cy, text=txt, fill="white", font=("Segoe UI", 9, "bold"))

    def _draw_pedals(self, gas, brake):
        self.cv_gas.delete("bar")
        w_gas = 160 * gas
        self.cv_gas.create_rectangle(0, 0, w_gas, 15, fill="#44FF44", outline="", tags="bar")

        self.cv_brake.delete("bar")
        w_brake = 160 * brake
        self.cv_brake.create_rectangle(0, 0, w_brake, 15, fill="#FF4444", outline="", tags="bar")

    def _draw_bb_bar(self, bb):
        self.cv_bb.delete("bar")
        width = 350
        if bb < 10 or bb > 90: return
        ratio = (bb - 48.0) / 20.0 
        ratio = max(0, min(1, ratio))
        x_pos = ratio * width
        self.cv_bb.create_rectangle(0, 0, width, 10, fill="#333", outline="") 
        self.cv_bb.create_rectangle(x_pos-2, 0, x_pos+2, 10, fill="#DDAA00", tags="bar", outline="white")

# ======================================================
# 6. EXECUÇÃO PRINCIPAL
# ======================================================
if __name__ == "__main__":
    telemetry_state = TelemetryData()
    reader = ACCReader(telemetry_state)
    reader.start()
    
    try:
        app = DashboardApp(telemetry_state)
        app.mainloop()
    finally:
        reader.stop()