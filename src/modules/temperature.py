# Módulo de Controle de Temperatura
# MAX6675 + Controle de Resistência

from machine import Pin
import utime
import time
from config import *

class TemperatureController:
    def __init__(self):
        # Configurar pinos MAX6675
        self.cs = Pin(MAX6675_CS_PIN, Pin.OUT)
        self.so = Pin(MAX6675_SO_PIN, Pin.IN)
        self.sck = Pin(MAX6675_SCK_PIN, Pin.OUT)
        
        # Configurar saída da resistência
        self.resistencia = Pin(RESISTENCIA_PIN, Pin.OUT)
        
        # Estado inicial
        self.cs.on()
        self.sck.off()
        self.resistencia.off()
        
        # Filtro de temperatura
        self.temp_history = []
        self.max_temp_reached = 0.0
        
        # Estado do controle
        self.heating_active = False
        self.error_count = 0
        self.last_valid_temp = TEMP_AMBIENTE
        
    def __read_bit(self):
        """Lê um bit do MAX6675"""
        self.sck.off()
        utime.sleep_us(1)
        bit = self.so.value()
        self.sck.on()
        utime.sleep_us(1)
        return bit
    
    def __read_word(self):
        """Lê 16 bits do MAX6675"""
        return [self.__read_bit() for _ in range(16)]
    
    def read_temperature_raw(self):
        """Lê temperatura bruta do MAX6675"""
        try:
            self.cs.off()
            utime.sleep_us(1)
            bits = self.__read_word()
            self.cs.on()
            
            # Converter bits para valor
            raw = 0
            for bit in bits:
                raw = (raw << 1) | bit
            
            # Verificar erro de termopar
            if raw & 0x4:
                return None
            
            # Converter para temperatura
            temp = (raw >> 3) * 0.25
            self.error_count = 0  # Reset contador de erros
            return temp
            
        except Exception as e:
            if DEBUG_MODE:
                print(f"Erro na leitura: {e}")
            self.error_count += 1
            return None
    
    def read_temperature_filtered(self):
        """Lê temperatura com filtro de média móvel"""
        temp = self.read_temperature_raw()
        
        if temp is not None:
            # Adicionar ao histórico
            self.temp_history.append(temp)
            if len(self.temp_history) > TEMP_FILTER_SIZE:
                self.temp_history.pop(0)
            
            # Calcular média
            filtered_temp = sum(self.temp_history) / len(self.temp_history)
            self.last_valid_temp = filtered_temp
            
            # Atualizar temperatura máxima
            if filtered_temp > self.max_temp_reached:
                self.max_temp_reached = filtered_temp
            
            return filtered_temp
        
        # Em caso de erro, usar última temperatura válida se recente
        if self.error_count < MAX_CICLOS_ERRO:
            return self.last_valid_temp
        
        return None
    
    def control_heating(self, current_temp, target_temp):
        """Controla aquecimento com histerese"""
        if current_temp is None:
            # Erro no sensor - desligar por segurança
            self.resistencia.off()
            self.heating_active = False
            return False
        
        # Verificação de segurança
        if current_temp > MAX_TEMP_SEGURANCA:
            self.resistencia.off()
            self.heating_active = False
            if DEBUG_MODE:
                print(f"ALERTA: Temperatura de segurança excedida! {current_temp}°C")
            return False
        
        # Controle com histerese
        if current_temp < (target_temp - HISTERESE):
            self.resistencia.on()
            self.heating_active = True
        elif current_temp > (target_temp + HISTERESE):
            self.resistencia.off()
            self.heating_active = False
        
        return True
    
    def is_temperature_reached(self, current_temp, target_temp):
        """Verifica se temperatura alvo foi atingida"""
        if current_temp is None:
            return False
        
        return abs(current_temp - target_temp) <= TEMP_TOLERANCE
    
    def emergency_stop(self):
        """Parada de emergência - desliga tudo"""
        self.resistencia.off()
        self.heating_active = False
        if DEBUG_MODE:
            print("PARADA DE EMERGÊNCIA ATIVADA")
    
    def get_status(self):
        """Retorna status atual do controle"""
        return {
            'heating': self.heating_active,
            'max_temp': self.max_temp_reached,
            'error_count': self.error_count,
            'last_temp': self.last_valid_temp
        }
    
    def reset_max_temperature(self):
        """Reset da temperatura máxima registrada"""
        self.max_temp_reached = 0.0
    
    def calibrate_sensor(self, known_temp):
        """Calibração básica do sensor (opcional)"""
        current_temp = self.read_temperature_raw()
        if current_temp is not None:
            offset = known_temp - current_temp
            if DEBUG_MODE:
                print(f"Offset de calibração calculado: {offset:.2f}°C")
            return offset
        return 0.0
    
    def get_temperature_trend(self, window=5):
        """Calcula tendência de temperatura (subindo/descendo)"""
        if len(self.temp_history) < window:
            return 0.0
        
        recent_temps = self.temp_history[-window:]
        if len(recent_temps) < 2:
            return 0.0
        
        # Tendência simples: diferença entre primeiro e último
        trend = recent_temps[-1] - recent_temps[0]
        return trend / (window - 1)  # Por amostra
    
    def cleanup(self):
        """Limpeza ao finalizar"""
        self.resistencia.off()
        self.heating_active = False 