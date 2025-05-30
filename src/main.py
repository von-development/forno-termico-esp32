# Controlador de Forno Simplificado
# ESP32 + MAX6675 + Display + Relé (SEM potenciômetros)

import time
from machine import Pin, I2C
import sys

# Importar configurações simplificadas
from config import *

# Tentar importar bibliotecas
try:
    from libs.ssd1306 import SSD1306_I2C
    DISPLAY_AVAILABLE = True
except ImportError:
    DISPLAY_AVAILABLE = False
    print("Aviso: Display não disponível")

class SimpleFurnaceController:
    def __init__(self, target_temp=DEFAULT_TARGET_TEMP, duration=DEFAULT_DURATION):
        # Parâmetros configuráveis
        self.target_temp = target_temp
        self.duration = duration
        
        # Inicializar hardware
        self.setup_hardware()
        
        # Estado do sistema
        self.current_temp = TEMP_AMBIENTE
        self.heating_active = False
        self.cycle_active = False
        self.temp_history = []
        self.max_temp_reached = 0.0
        
        print("=== CONTROLADOR DE FORNO SIMPLIFICADO ===")
        print(f"Temperatura alvo: {self.target_temp}°C")
        print(f"Duração: {self.duration}s ({self.duration//60}min)")
        
    def setup_hardware(self):
        """Configurar hardware básico"""
        # MAX6675
        self.cs = Pin(MAX6675_CS_PIN, Pin.OUT)
        self.so = Pin(MAX6675_SO_PIN, Pin.IN)
        self.sck = Pin(MAX6675_SCK_PIN, Pin.OUT)
        
        # Estado inicial MAX6675
        self.cs.on()
        self.sck.off()
        
        # Controle do relé (forno)
        self.relay = Pin(RESISTENCIA_PIN, Pin.OUT)
        self.relay.off()  # Iniciar desligado
        
        # LED indicador
        self.led = Pin(LED_CICLO_PIN, Pin.OUT)
        self.led.off()
        
        # Display OLED
        if DISPLAY_AVAILABLE:
            try:
                i2c = I2C(0, scl=Pin(OLED_SCL_PIN), sda=Pin(OLED_SDA_PIN))
                self.display = SSD1306_I2C(OLED_WIDTH, OLED_HEIGHT, i2c)
                self.display_ok = True
                print("✓ Display OLED inicializado")
            except Exception as e:
                self.display_ok = False
                print(f"✗ Erro no display: {e}")
        else:
            self.display_ok = False
        
        print("✓ Hardware configurado")
    
    def read_temperature(self):
        """Ler temperatura do MAX6675"""
        try:
            # Protocolo SPI manual para MAX6675
            self.cs.off()
            time.sleep_us(1)
            
            # Ler 16 bits
            raw_data = 0
            for i in range(16):
                self.sck.off()
                time.sleep_us(1)
                bit = self.so.value()
                self.sck.on()
                time.sleep_us(1)
                raw_data = (raw_data << 1) | bit
            
            self.cs.on()
            
            # Verificar erro
            if raw_data & 0x4:
                return None
            
            # Converter para temperatura
            temp = (raw_data >> 3) * 0.25
            
            # Filtro de média móvel
            self.temp_history.append(temp)
            if len(self.temp_history) > TEMP_FILTER_SIZE:
                self.temp_history.pop(0)
            
            filtered_temp = sum(self.temp_history) / len(self.temp_history)
            self.current_temp = filtered_temp
            
            # Atualizar máxima
            if filtered_temp > self.max_temp_reached:
                self.max_temp_reached = filtered_temp
            
            return filtered_temp
            
        except Exception as e:
            print(f"Erro na leitura: {e}")
            return None
    
    def control_heating(self):
        """Controlar aquecimento com histerese"""
        if self.current_temp is None:
            self.relay.off()
            self.heating_active = False
            return False
        
        # Verificação de segurança
        if self.current_temp > MAX_TEMP_SEGURANCA:
            self.relay.off()
            self.heating_active = False
            print(f"⚠️ ALERTA: Temperatura de segurança excedida! {self.current_temp:.1f}°C")
            return False
        
        # Controle com histerese
        if self.current_temp < (self.target_temp - HISTERESE):
            if RELAY_ACTIVE_HIGH:
                self.relay.on()
            else:
                self.relay.off()
            self.heating_active = True
        elif self.current_temp > (self.target_temp + HISTERESE):
            if RELAY_ACTIVE_HIGH:
                self.relay.off()
            else:
                self.relay.on()
            self.heating_active = False
        
        return True
    
    def update_display(self, phase="", elapsed_time=0, remaining_time=0):
        """Atualizar display OLED"""
        if not self.display_ok:
            return
        
        try:
            self.display.fill(0)
            
            # Título
            if phase:
                self.display.text(phase, 0, 0)
            
            # Temperaturas
            self.display.text(f"PV:{self.current_temp:.1f}C", 0, 15)
            self.display.text(f"SP:{self.target_temp:.1f}C", 65, 15)
            
            # Status aquecimento
            status = "ON " if self.heating_active else "OFF"
            self.display.text(f"Aquec:{status}", 0, 25)
            
            # Tempos
            if elapsed_time > 0:
                min_e = int(elapsed_time // 60)
                sec_e = int(elapsed_time % 60)
                self.display.text(f"T:{min_e:02d}:{sec_e:02d}", 0, 35)
            
            if remaining_time > 0:
                min_r = int(remaining_time // 60)
                sec_r = int(remaining_time % 60)
                self.display.text(f"R:{min_r:02d}:{sec_r:02d}", 65, 35)
            
            # Temperatura máxima
            self.display.text(f"Max:{self.max_temp_reached:.1f}C", 0, 50)
            
            self.display.show()
            
        except Exception as e:
            print(f"Erro no display: {e}")
    
    def log_data(self, phase, elapsed_time):
        """Registrar dados em arquivo"""
        try:
            timestamp = time.localtime()
            with open(LOG_FILENAME, "a") as f:
                f.write(f"{timestamp[0]:04d}-{timestamp[1]:02d}-{timestamp[2]:02d} ")
                f.write(f"{timestamp[3]:02d}:{timestamp[4]:02d}:{timestamp[5]:02d},")
                f.write(f"{phase},{self.current_temp:.2f},{self.target_temp:.1f},")
                f.write(f"{self.heating_active},{elapsed_time:.0f}\n")
        except Exception as e:
            print(f"Erro no log: {e}")
    
    def run_cycle(self):
        """Executar ciclo completo de tratamento"""
        print("\n=== INICIANDO CICLO DE TRATAMENTO ===")
        print(f"Temperatura alvo: {self.target_temp}°C")
        print(f"Duração: {self.duration}s")
        print("Pressione Ctrl+C para parar\n")
        
        # Inicializar ciclo
        self.cycle_active = True
        self.led.on()
        self.max_temp_reached = 0.0
        
        try:
            # FASE 1: Aquecimento
            print("--- FASE 1: AQUECIMENTO ---")
            phase1_start = time.time()
            last_log = 0
            
            while True:
                current_time = time.time()
                elapsed = current_time - phase1_start
                
                # Ler temperatura
                temp = self.read_temperature()
                if temp is None:
                    print("Erro na leitura do sensor!")
                    break
                
                # Controlar aquecimento
                control_ok = self.control_heating()
                if not control_ok:
                    break
                
                # Mostrar status
                if PRINT_TEMPERATURE:
                    status = "AQUECENDO" if self.heating_active else "MANTENDO"
                    print(f"T:{temp:.1f}°C | Alvo:{self.target_temp:.1f}°C | {status} | {elapsed:.0f}s")
                
                # Atualizar display
                self.update_display("FASE 1 - AQUEC", elapsed)
                
                # Log periódico
                if elapsed - last_log >= LOG_INTERVAL:
                    self.log_data("FASE1", elapsed)
                    last_log = elapsed
                
                # Verificar se atingiu temperatura
                if abs(temp - self.target_temp) <= TEMP_TOLERANCE:
                    print(f"✓ Temperatura atingida: {temp:.1f}°C")
                    break
                
                # Verificar timeout
                if elapsed > FASE1_TIMEOUT:
                    print("⚠️ Timeout na Fase 1 - não conseguiu atingir temperatura")
                    break
                
                time.sleep(TEMP_READ_INTERVAL)
            
            # FASE 2: Tratamento
            print("\n--- FASE 2: TRATAMENTO ---")
            phase2_start = time.time()
            last_log = 0
            
            while True:
                current_time = time.time()
                elapsed = current_time - phase2_start
                remaining = self.duration - elapsed
                
                if elapsed >= self.duration:
                    print("✓ Tratamento concluído!")
                    break
                
                # Ler temperatura
                temp = self.read_temperature()
                if temp is None:
                    print("Erro na leitura do sensor!")
                    break
                
                # Controlar aquecimento
                control_ok = self.control_heating()
                if not control_ok:
                    break
                
                # Mostrar status
                if PRINT_TEMPERATURE:
                    status = "AQUECENDO" if self.heating_active else "MANTENDO"
                    print(f"T:{temp:.1f}°C | Alvo:{self.target_temp:.1f}°C | {status} | Restam:{remaining:.0f}s")
                
                # Atualizar display
                self.update_display("FASE 2 - TRAT", elapsed, remaining)
                
                # Log periódico
                if elapsed - last_log >= LOG_INTERVAL:
                    self.log_data("FASE2", elapsed)
                    last_log = elapsed
                
                time.sleep(TEMP_READ_INTERVAL)
            
        except KeyboardInterrupt:
            print("\n🛑 Ciclo interrompido pelo usuário")
        except Exception as e:
            print(f"\n❌ Erro durante o ciclo: {e}")
        finally:
            # Finalizar ciclo
            self.stop_cycle()
    
    def stop_cycle(self):
        """Parar ciclo e desligar tudo"""
        print("\n=== FINALIZANDO CICLO ===")
        
        # Desligar tudo
        self.relay.off()
        self.led.off()
        self.heating_active = False
        self.cycle_active = False
        
        # Relatório final
        print(f"Temperatura máxima atingida: {self.max_temp_reached:.1f}°C")
        print(f"Temperatura final: {self.current_temp:.1f}°C")
        
        # Atualizar display
        if self.display_ok:
            try:
                self.display.fill(0)
                self.display.text("CICLO FINALIZADO", 5, 0)
                self.display.text(f"Max:{self.max_temp_reached:.1f}C", 0, 20)
                self.display.text(f"Final:{self.current_temp:.1f}C", 0, 35)
                self.display.show()
            except:
                pass
        
        print("✓ Ciclo finalizado com segurança")

# Funções auxiliares para configuração
def set_temperature(temp):
    """Definir nova temperatura alvo"""
    if TEMP_MIN <= temp <= TEMP_MAX:
        return temp
    else:
        print(f"❌ Temperatura deve estar entre {TEMP_MIN}°C e {TEMP_MAX}°C")
        return DEFAULT_TARGET_TEMP

def set_duration(duration):
    """Definir nova duração"""
    if DURACAO_MIN <= duration <= DURACAO_MAX:
        return duration
    else:
        print(f"❌ Duração deve estar entre {DURACAO_MIN}s e {DURACAO_MAX}s")
        return DEFAULT_DURATION

# Menu interativo
def interactive_menu():
    """Menu interativo para configurar e executar"""
    print("\n=== MENU DO CONTROLADOR DE FORNO ===")
    print("1. Executar com valores padrão")
    print("2. Configurar temperatura e duração")
    print("3. Teste rápido (leitura de temperatura)")
    print("4. Sair")
    
    choice = input("Escolha uma opção (1-4): ").strip()
    
    if choice == "1":
        # Executar com padrões
        furnace = SimpleFurnaceController()
        furnace.run_cycle()
        
    elif choice == "2":
        # Configurar manualmente
        try:
            temp = float(input(f"Temperatura desejada ({TEMP_MIN}-{TEMP_MAX}°C): "))
            temp = set_temperature(temp)
            
            duration = int(input(f"Duração em segundos ({DURACAO_MIN}-{DURACAO_MAX}s): "))
            duration = set_duration(duration)
            
            furnace = SimpleFurnaceController(temp, duration)
            furnace.run_cycle()
            
        except ValueError:
            print("❌ Valores inválidos!")
            
    elif choice == "3":
        # Teste de temperatura
        print("\n=== TESTE DE TEMPERATURA ===")
        furnace = SimpleFurnaceController()
        
        for i in range(10):
            temp = furnace.read_temperature()
            if temp:
                print(f"Leitura {i+1}: {temp:.2f}°C")
            else:
                print(f"Leitura {i+1}: ERRO")
            time.sleep(1)
        
        furnace.stop_cycle()
        
    elif choice == "4":
        print("Saindo...")
        return False
    else:
        print("❌ Opção inválida!")
    
    return True

# Programa principal
if __name__ == "__main__":
    try:
        while interactive_menu():
            pass
    except KeyboardInterrupt:
        print("\nPrograma interrompido")
    except Exception as e:
        print(f"Erro: {e}") 
