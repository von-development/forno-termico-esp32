# Módulo de Gerenciamento de Entradas
# Botões, Potenciômetros e Controle por Teclado

from machine import Pin, ADC
import time
import sys
import select
from config import *

class InputManager:
    def __init__(self, control_mode=DEFAULT_CONTROL_MODE):
        self.control_mode = control_mode
        
        # Inicializar entradas analógicas
        self.temp_ref_adc = ADC(Pin(TEMP_REF_PIN))
        self.duracao_adc = ADC(Pin(DURACAO_PIN))
        
        # Inicializar botões
        self.btn_start = Pin(BTN_START_PIN, Pin.IN, Pin.PULL_UP)
        self.btn_stop = Pin(BTN_STOP_PIN, Pin.IN, Pin.PULL_UP)
        
        # Estado dos botões para debounce
        self.btn_start_last = True
        self.btn_stop_last = True
        self.last_btn_time = 0
        self.debounce_delay = 0.2  # 200ms
        
    def map_adc_value(self, adc_value, min_val, max_val):
        """Mapeia valor ADC (0-4095) para range desejado"""
        return min_val + (adc_value / 4095.0) * (max_val - min_val)
    
    def read_temperature_setpoint(self):
        """Lê temperatura desejada do potenciômetro"""
        adc_val = self.temp_ref_adc.read()
        temp = self.map_adc_value(adc_val, TEMP_MIN, TEMP_MAX)
        return round(temp, 1)
    
    def read_duration_setpoint(self):
        """Lê duração desejada do potenciômetro"""
        adc_val = self.duracao_adc.read()
        duration = self.map_adc_value(adc_val, DURACAO_MIN, DURACAO_MAX)
        return int(duration)
    
    def button_pressed(self, button):
        """Verifica se botão foi pressionado com debounce"""
        current_time = time.time()
        if current_time - self.last_btn_time < self.debounce_delay:
            return False
        
        current_state = button.value()
        
        if button == self.btn_start:
            if not current_state and self.btn_start_last:
                self.last_btn_time = current_time
                self.btn_start_last = current_state
                return True
            self.btn_start_last = current_state
            
        elif button == self.btn_stop:
            if not current_state and self.btn_stop_last:
                self.last_btn_time = current_time
                self.btn_stop_last = current_state
                return True
            self.btn_stop_last = current_state
            
        return False
    
    def check_start_command(self):
        """Verifica comando de início baseado no modo de controle"""
        if self.control_mode == CONTROL_MODE_BUTTON:
            return self.button_pressed(self.btn_start)
        
        elif self.control_mode == CONTROL_MODE_KEYBOARD:
            return self.check_keyboard_input('s')  # 's' para start
        
        return False
    
    def check_stop_command(self):
        """Verifica comando de parada baseado no modo de controle"""
        if self.control_mode == CONTROL_MODE_BUTTON:
            return self.button_pressed(self.btn_stop)
        
        elif self.control_mode == CONTROL_MODE_KEYBOARD:
            return self.check_keyboard_input('q')  # 'q' para quit/stop
        
        return False
    
    def check_keyboard_input(self, expected_key=None):
        """Verifica entrada do teclado (non-blocking)"""
        try:
            # Verificar se há entrada disponível
            if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                key = sys.stdin.read(1).lower()
                if expected_key:
                    return key == expected_key
                return key
        except:
            # Em alguns ambientes pode não funcionar
            return False
        return False
    
    def wait_for_start_command(self, display_callback=None):
        """Aguarda comando de início"""
        print("=== CONTROLE DO FORNO ===")
        if self.control_mode == CONTROL_MODE_KEYBOARD:
            print("Pressione 's' para INICIAR o ciclo")
            print("Pressione 'q' para SAIR")
        else:
            print("Pressione o BOTÃO START para iniciar")
            print("Pressione o BOTÃO STOP para sair")
        
        while True:
            # Atualizar display se callback fornecido
            if display_callback:
                temp_sp = self.read_temperature_setpoint()
                duration_sp = self.read_duration_setpoint()
                display_callback(temp_sp, duration_sp)
            
            # Verificar comando de início
            if self.check_start_command():
                return True
            
            # Verificar comando de saída
            if self.check_stop_command():
                return False
            
            time.sleep(0.1)
    
    def get_treatment_parameters(self):
        """Obtém parâmetros do tratamento"""
        temp_setpoint = self.read_temperature_setpoint()
        duration_setpoint = self.read_duration_setpoint()
        
        # Validar parâmetros
        temp_setpoint = max(TEMP_MIN, min(TEMP_MAX, temp_setpoint))
        duration_setpoint = max(DURACAO_MIN, min(DURACAO_MAX, duration_setpoint))
        
        return temp_setpoint, duration_setpoint
    
    def show_control_help(self):
        """Mostra ajuda sobre controles disponíveis"""
        print("\n=== AJUDA DE CONTROLES ===")
        print(f"Modo atual: {self.control_mode}")
        
        if self.control_mode == CONTROL_MODE_KEYBOARD:
            print("Comandos do teclado:")
            print("  's' - Iniciar ciclo")
            print("  'q' - Parar/Sair")
            print("  'h' - Mostrar ajuda")
        else:
            print("Controles físicos:")
            print(f"  GPIO {BTN_START_PIN} - Botão START")
            print(f"  GPIO {BTN_STOP_PIN} - Botão STOP")
        
        print("Potenciômetros:")
        print(f"  GPIO {TEMP_REF_PIN} - Temperatura ({TEMP_MIN}-{TEMP_MAX}°C)")
        print(f"  GPIO {DURACAO_PIN} - Duração ({DURACAO_MIN}-{DURACAO_MAX}s)")
        print("==========================\n")
    
    def set_control_mode(self, mode):
        """Altera modo de controle"""
        if mode in [CONTROL_MODE_KEYBOARD, CONTROL_MODE_BUTTON]:
            self.control_mode = mode
            print(f"Modo de controle alterado para: {mode}")
        else:
            print("Modo inválido! Use 'keyboard' ou 'button'") 