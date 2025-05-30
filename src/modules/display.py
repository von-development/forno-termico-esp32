# Módulo de Gerenciamento do Display OLED
# SSD1306 128x64

from machine import I2C, Pin
import time
import utime
from libs.ssd1306 import SSD1306_I2C
from config import *

class DisplayManager:
    def __init__(self):
        # Configurar I2C
        self.i2c = I2C(0, scl=Pin(OLED_SCL_PIN), sda=Pin(OLED_SDA_PIN))
        
        # Inicializar display
        try:
            self.oled = SSD1306_I2C(OLED_WIDTH, OLED_HEIGHT, self.i2c)
            self.display_available = True
            self.show_startup_screen()
        except Exception as e:
            print(f"Erro ao inicializar display: {e}")
            self.display_available = False
            self.oled = None
    
    def clear(self):
        """Limpa o display"""
        if self.display_available:
            self.oled.fill(0)
    
    def show(self):
        """Atualiza o display"""
        if self.display_available:
            self.oled.show()
    
    def write_text(self, text, x, y):
        """Escreve texto no display"""
        if self.display_available:
            self.oled.text(str(text), x, y)
    
    def show_startup_screen(self):
        """Tela de inicialização"""
        self.clear()
        self.write_text("FORNO TERMICO", 15, 10)
        self.write_text("ESP32 + MAX6675", 5, 25)
        self.write_text("IEA 2024-2025", 15, 40)
        self.show()
        time.sleep(2)
    
    def show_waiting_screen(self, temp_sp, duration_sp, control_mode):
        """Tela de espera por comando"""
        self.clear()
        self.write_text("AGUARDANDO", 20, 0)
        
        # Mostrar setpoints
        self.write_text(f"Temp: {temp_sp:.1f}C", 0, 15)
        self.write_text(f"Dur: {duration_sp}s", 0, 25)
        
        # Modo de controle
        mode_text = "BTN" if control_mode == CONTROL_MODE_BUTTON else "TEC"
        self.write_text(f"Modo: {mode_text}", 0, 35)
        
        # Instrução
        if control_mode == CONTROL_MODE_BUTTON:
            self.write_text("Press START", 25, 50)
        else:
            self.write_text("Press 's'", 30, 50)
        
        self.show()
    
    def show_heating_screen(self, current_temp, target_temp, heating_on, elapsed_time):
        """Tela durante aquecimento (Fase 1)"""
        self.clear()
        self.write_text("FASE 1 - AQUEC", 5, 0)
        
        # Temperaturas
        self.write_text(f"PV:{current_temp:.1f}C", 0, 15)
        self.write_text(f"SP:{target_temp:.1f}C", 65, 15)
        
        # Status do aquecimento
        status = "ON " if heating_on else "OFF"
        self.write_text(f"Aquec: {status}", 0, 25)
        
        # Tempo decorrido
        minutes = int(elapsed_time // 60)
        seconds = int(elapsed_time % 60)
        self.write_text(f"T: {minutes:02d}:{seconds:02d}", 0, 35)
        
        # Barra de progresso (visual da temperatura)
        if target_temp > 0:
            progress = min(current_temp / target_temp, 1.0) * 100
            self.write_text(f"Prog:{progress:.0f}%", 0, 45)
        
        self.show()
    
    def show_treatment_screen(self, current_temp, target_temp, heating_on, 
                            elapsed_time, remaining_time):
        """Tela durante tratamento (Fase 2)"""
        self.clear()
        self.write_text("FASE 2 - TRAT", 5, 0)
        
        # Temperaturas
        self.write_text(f"PV:{current_temp:.1f}C", 0, 12)
        self.write_text(f"SP:{target_temp:.1f}C", 65, 12)
        
        # Status do aquecimento
        status = "ON " if heating_on else "OFF"
        self.write_text(f"Aquec: {status}", 0, 22)
        
        # Tempo decorrido
        elapsed_min = int(elapsed_time // 60)
        elapsed_sec = int(elapsed_time % 60)
        self.write_text(f"Dec:{elapsed_min:02d}:{elapsed_sec:02d}", 0, 32)
        
        # Tempo restante
        remain_min = int(remaining_time // 60)
        remain_sec = int(remaining_time % 60)
        self.write_text(f"Rest:{remain_min:02d}:{remain_sec:02d}", 0, 42)
        
        # Barra de progresso do tempo
        if elapsed_time + remaining_time > 0:
            progress = elapsed_time / (elapsed_time + remaining_time) * 100
            self.write_text(f"[{int(progress/10)*'=':<10}]", 0, 52)
        
        self.show()
    
    def show_completed_screen(self, max_temp, total_time):
        """Tela de ciclo finalizado"""
        self.clear()
        self.write_text("CICLO COMPLETO", 5, 0)
        
        # Temperatura máxima atingida
        self.write_text(f"Max: {max_temp:.1f}C", 0, 15)
        
        # Tempo total
        total_min = int(total_time // 60)
        total_sec = int(total_time % 60)
        self.write_text(f"Tempo: {total_min}:{total_sec:02d}", 0, 25)
        
        # Data/hora
        current_time = time.localtime()
        time_str = f"{current_time[3]:02d}:{current_time[4]:02d}"
        self.write_text(f"Fim: {time_str}", 0, 35)
        
        self.write_text("Pressione para", 10, 50)
        self.write_text("novo ciclo", 20, 58)
        
        self.show()
    
    def show_error_screen(self, error_msg):
        """Tela de erro"""
        self.clear()
        self.write_text("ERRO!", 45, 0)
        
        # Dividir mensagem em linhas se necessário
        if len(error_msg) > 16:
            line1 = error_msg[:16]
            line2 = error_msg[16:32] if len(error_msg) > 16 else ""
            self.write_text(line1, 0, 20)
            if line2:
                self.write_text(line2, 0, 30)
        else:
            self.write_text(error_msg, 0, 20)
        
        self.write_text("Verificar", 25, 45)
        self.write_text("conexoes", 25, 55)
        
        self.show()
    
    def show_date_time(self):
        """Mostra data e hora atual"""
        if not self.display_available:
            return
        
        current_time = time.localtime()
        date_str = f"{current_time[2]:02d}/{current_time[1]:02d}/{current_time[0]}"
        time_str = f"{current_time[3]:02d}:{current_time[4]:02d}:{current_time[5]:02d}"
        
        self.clear()
        self.write_text("DATA/HORA", 25, 0)
        self.write_text(date_str, 15, 25)
        self.write_text(time_str, 20, 40)
        self.show()
        time.sleep(3)
    
    def show_parameters_screen(self, temp_sp, duration_sp):
        """Mostra parâmetros configurados"""
        self.clear()
        self.write_text("PARAMETROS", 20, 0)
        
        self.write_text(f"Temperatura:", 0, 15)
        self.write_text(f"{temp_sp:.1f} C", 0, 25)
        
        self.write_text(f"Duracao:", 0, 35)
        duration_min = duration_sp // 60
        duration_sec = duration_sp % 60
        self.write_text(f"{duration_min}m {duration_sec}s", 0, 45)
        
        self.show()
    
    def show_safety_warning(self, temp):
        """Mostra aviso de segurança"""
        self.clear()
        self.write_text("!!! ALERTA !!!", 5, 0)
        self.write_text("SOBREAQUECIMENTO", 0, 15)
        self.write_text(f"Temp: {temp:.1f}C", 0, 30)
        self.write_text("SISTEMA PARADO", 5, 45)
        self.show()
        
        # Piscar para chamar atenção
        for _ in range(3):
            time.sleep(0.5)
            self.clear()
            self.show()
            time.sleep(0.5)
            self.show_safety_warning(temp)
    
    def is_available(self):
        """Verifica se display está disponível"""
        return self.display_available 