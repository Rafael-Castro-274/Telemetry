"""
Instalador Gráfico - Corredor X
Interface Windows para instalação automatizada
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import subprocess
import sys
import os
import threading

class InstaladorCorredorX:
    def __init__(self, root):
        self.root = root
        self.root.title("Corredor X - Instalador")
        self.root.geometry("600x500")
        self.root.resizable(False, False)
        
        # Cor de fundo
        self.root.configure(bg="#1e1e1e")
        
        # Estilo
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TButton", padding=10, font=("Segoe UI", 10))
        style.configure("TLabel", background="#1e1e1e", foreground="white", font=("Segoe UI", 10))
        
        self.criar_interface()
        
    def criar_interface(self):
        # Frame principal
        main_frame = tk.Frame(self.root, bg="#1e1e1e")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Título
        title_label = tk.Label(
            main_frame,
            text="🏎️ CORREDOR X",
            font=("Segoe UI", 24, "bold"),
            bg="#1e1e1e",
            fg="#00ff00"
        )
        title_label.pack(pady=(0, 5))
        
        subtitle_label = tk.Label(
            main_frame,
            text="Sistema de Telemetria ACC",
            font=("Segoe UI", 12),
            bg="#1e1e1e",
            fg="#888888"
        )
        subtitle_label.pack(pady=(0, 20))
        
        # Informações
        info_frame = tk.Frame(main_frame, bg="#2d2d2d", relief=tk.RIDGE, bd=2)
        info_frame.pack(fill=tk.X, pady=(0, 20))
        
        info_text = """
📦 O que será instalado:
  • matplotlib (gráficos em tempo real)
  • numpy (cálculos matemáticos)
  
📁 Localização: {}
        """.format(os.getcwd())
        
        info_label = tk.Label(
            info_frame,
            text=info_text,
            font=("Consolas", 9),
            bg="#2d2d2d",
            fg="white",
            justify=tk.LEFT,
            padx=15,
            pady=15
        )
        info_label.pack()
        
        # Opções de instalação
        options_frame = tk.Frame(main_frame, bg="#1e1e1e")
        options_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.use_venv = tk.BooleanVar(value=True)
        venv_check = tk.Checkbutton(
            options_frame,
            text="Usar Ambiente Virtual (Recomendado)",
            variable=self.use_venv,
            bg="#1e1e1e",
            fg="white",
            selectcolor="#2d2d2d",
            font=("Segoe UI", 10),
            activebackground="#1e1e1e",
            activeforeground="white"
        )
        venv_check.pack(anchor=tk.W)
        
        # Área de log
        log_label = tk.Label(
            main_frame,
            text="📋 Log de Instalação:",
            font=("Segoe UI", 10, "bold"),
            bg="#1e1e1e",
            fg="white"
        )
        log_label.pack(anchor=tk.W, pady=(0, 5))
        
        self.log_text = scrolledtext.ScrolledText(
            main_frame,
            height=10,
            bg="#0d0d0d",
            fg="#00ff00",
            font=("Consolas", 9),
            insertbackground="white"
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Barra de progresso
        self.progress = ttk.Progressbar(
            main_frame,
            mode='indeterminate',
            length=560
        )
        self.progress.pack(pady=(0, 15))
        
        # Botões
        button_frame = tk.Frame(main_frame, bg="#1e1e1e")
        button_frame.pack(fill=tk.X)
        
        self.install_button = tk.Button(
            button_frame,
            text="🚀 INSTALAR",
            command=self.iniciar_instalacao,
            bg="#00aa00",
            fg="white",
            font=("Segoe UI", 11, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            height=2,
            activebackground="#00ff00"
        )
        self.install_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 3))
        
        self.run_button = tk.Button(
            button_frame,
            text="▶️ EXECUTAR",
            command=self.executar_programa,
            bg="#0066cc",
            fg="white",
            font=("Segoe UI", 11, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            height=2,
            state=tk.DISABLED,
            activebackground="#0088ff"
        )
        self.run_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(3, 3))
        
        self.close_button = tk.Button(
            button_frame,
            text="❌ FECHAR",
            command=self.root.quit,
            bg="#aa0000",
            fg="white",
            font=("Segoe UI", 11, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            height=2,
            activebackground="#ff0000"
        )
        self.close_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(3, 0))
        
    def log(self, mensagem):
        self.log_text.insert(tk.END, mensagem + "\n")
        self.log_text.see(tk.END)
        self.root.update()
        
    def executar_comando(self, comando):
        try:
            process = subprocess.Popen(
                comando,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True,
                text=True
            )
            
            for line in process.stdout:
                self.log(line.strip())
            
            process.wait()
            
            if process.returncode != 0:
                error = process.stderr.read()
                self.log(f"❌ ERRO: {error}")
                return False
            return True
            
        except Exception as e:
            self.log(f"❌ EXCEÇÃO: {str(e)}")
            return False
    
    def executar_programa(self):
        """Executa o programa Corredor X após instalação"""
        self.log("\n" + "=" * 60)
        self.log("▶️ INICIANDO CORREDOR X...")
        self.log("=" * 60)
        
        try:
            if os.path.exists("executar.bat"):
                subprocess.Popen(["executar.bat"], shell=True)
                self.log("✅ Programa iniciado!")
                self.log("⚠️ Certifique-se de que o ACC está rodando")
            else:
                # Executar diretamente
                if os.path.exists("venv"):
                    python_path = os.path.join("venv", "Scripts", "python.exe")
                else:
                    python_path = sys.executable
                
                subprocess.Popen([python_path, "corredorx.py"])
                self.log("✅ Programa iniciado!")
                self.log("⚠️ Certifique-se de que o ACC está rodando")
        except Exception as e:
            self.log(f"❌ Erro ao executar: {e}")
            messagebox.showerror("Erro", f"Não foi possível executar o programa:\n{e}")
    
    def instalar(self):
        self.install_button.config(state=tk.DISABLED)
        self.run_button.config(state=tk.DISABLED)
        self.close_button.config(state=tk.DISABLED)
        self.progress.start()
        
        self.log("=" * 60)
        self.log("🏎️ CORREDOR X - INICIANDO INSTALAÇÃO")
        self.log("=" * 60)
        self.log("")
        
        sucesso = True
        
        # Verificar Python
        self.log("🔍 Verificando Python...")
        resultado = subprocess.run([sys.executable, "--version"], capture_output=True, text=True)
        self.log(f"✅ {resultado.stdout.strip()}")
        self.log("")
        
        # Criar pastas
        self.log("📁 Criando estrutura de pastas...")
        for pasta in ["dados", "relatorios"]:
            os.makedirs(pasta, exist_ok=True)
            self.log(f"✅ Pasta '{pasta}' criada/verificada")
        self.log("")
        
        # Ambiente virtual
        if self.use_venv.get():
            self.log("🔧 Criando ambiente virtual...")
            if not self.executar_comando(f"{sys.executable} -m venv venv"):
                sucesso = False
            else:
                self.log("✅ Ambiente virtual criado")
                self.log("")
                
                # Ativar venv
                if os.name == 'nt':  # Windows
                    pip_path = os.path.join("venv", "Scripts", "pip.exe")
                else:
                    pip_path = os.path.join("venv", "bin", "pip")
        else:
            pip_path = "pip"
        
        # Atualizar pip
        if sucesso:
            self.log("📦 Atualizando pip...")
            if self.use_venv.get():
                comando = f"{pip_path} install --upgrade pip"
            else:
                comando = f"{sys.executable} -m pip install --upgrade pip"
            
            self.executar_comando(comando)
            self.log("")
        
        # Instalar dependências
        if sucesso:
            self.log("📦 Instalando dependências (isso pode demorar)...")
            if self.use_venv.get():
                comando = f"{pip_path} install -r requirements.txt"
            else:
                comando = f"{sys.executable} -m pip install -r requirements.txt"
            
            if not self.executar_comando(comando):
                sucesso = False
            else:
                self.log("")
                self.log("✅ Todas as dependências instaladas com sucesso!")
        
        self.progress.stop()
        self.log("")
        self.log("=" * 60)
        
        if sucesso:
            self.log("🎉 INSTALAÇÃO CONCLUÍDA COM SUCESSO!")
            self.log("=" * 60)
            self.log("")
            self.log("▶️ Clique em 'EXECUTAR' para iniciar o programa")
            self.log("   ou feche e use: executar.bat")
            
            # Habilitar botão EXECUTAR
            self.run_button.config(state=tk.NORMAL, bg="#00aa00")
            
            messagebox.showinfo(
                "Instalação Concluída",
                "✅ Corredor X instalado com sucesso!\n\n"
                "Clique em 'EXECUTAR' para iniciar!"
            )
        else:
            self.log("❌ INSTALAÇÃO FALHOU")
            self.log("=" * 60)
            messagebox.showerror(
                "Erro na Instalação",
                "❌ Ocorreram erros durante a instalação.\n"
                "Verifique o log acima para mais detalhes."
            )
        
        self.install_button.config(state=tk.NORMAL)
        self.close_button.config(state=tk.NORMAL)
    
    def iniciar_instalacao(self):
        resposta = messagebox.askyesno(
            "Confirmar Instalação",
            "Deseja instalar o Corredor X e suas dependências?"
        )
        
        if resposta:
            # Executar em thread separada para não travar a interface
            thread = threading.Thread(target=self.instalar)
            thread.daemon = True
            thread.start()

def main():
    root = tk.Tk()
    app = InstaladorCorredorX(root)
    
    # Centralizar janela
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    root.mainloop()

if __name__ == "__main__":
    main()
