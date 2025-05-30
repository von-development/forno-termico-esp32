# Configuração Simplificada - Sem Potenciômetros
# ESP32 + MAX6675 + Display + Relé + LED

# === CONFIGURAÇÕES DE HARDWARE ===

# MAX6675 (Termopar)
MAX6675_CS_PIN = 23    # Chip Select
MAX6675_SO_PIN = 19    # Serial Output (MISO)
MAX6675_SCK_PIN = 5    # Serial Clock

# Display OLED SSD1306
OLED_SDA_PIN = 21      # I2C Data
OLED_SCL_PIN = 22      # I2C Clock
OLED_WIDTH = 128       # Largura do display
OLED_HEIGHT = 64       # Altura do display

# Saídas Digitais
RESISTENCIA_PIN = 18   # Controle do relé (forno)
LED_CICLO_PIN = 4      # LED indicador de ciclo

# === CONFIGURAÇÕES DE CONTROLE ===

# Temperaturas padrão (configuráveis via código)
TEMP_MIN = 20.0        # Temperatura mínima (°C)
TEMP_MAX = 300.0       # Temperatura máxima (°C)
TEMP_AMBIENTE = 25.0   # Temperatura ambiente padrão (°C)

# Durações padrão (configuráveis via código)
DURACAO_MIN = 30       # Duração mínima (segundos)
DURACAO_MAX = 3600     # Duração máxima (segundos)

# Controle de Histerese
HISTERESE = 2.0        # Margem de controle (°C)
TEMP_FILTER_SIZE = 5   # Tamanho do filtro de média móvel

# Fases de Tratamento
FASE1_TIMEOUT = 600    # Timeout para atingir temperatura (segundos)
TEMP_TOLERANCE = 1.0   # Tolerância para considerar temperatura atingida (°C)

# === CONFIGURAÇÕES FIXAS PARA OPERAÇÃO MANUAL ===

# Valores padrão que serão alterados via código
DEFAULT_TARGET_TEMP = 100.0    # Temperatura padrão
DEFAULT_DURATION = 300         # Duração padrão (5 minutos)

# === CONFIGURAÇÕES DE INTERFACE ===

# Apenas modo teclado (sem botões físicos)
DEFAULT_CONTROL_MODE = "keyboard"

# Intervalos de atualização
DISPLAY_UPDATE_INTERVAL = 1.0      # Atualização do display (segundos)
TEMP_READ_INTERVAL = 0.5           # Leitura de temperatura (segundos)
LOG_INTERVAL = 10.0                # Intervalo de log (segundos)

# === CONFIGURAÇÕES DE SEGURANÇA ===

# Limites de segurança
MAX_TEMP_SEGURANCA = 350.0     # Temperatura máxima absoluta (°C)
TIMEOUT_SENSOR = 5.0           # Timeout para leitura do sensor (segundos)
MAX_CICLOS_ERRO = 3            # Máximo de erros consecutivos

# === CONFIGURAÇÕES DE DEBUG ===

DEBUG_MODE = True              # Ativar mensagens de debug
VERBOSE_LOGGING = True         # Log detalhado
PRINT_TEMPERATURE = True       # Imprimir temperatura no console

# === CONFIGURAÇÕES DE ARQUIVOS ===

LOG_FILENAME = "tratamentos_log.txt"

# === CONFIGURAÇÕES ESPECÍFICAS PARA MÓDULO RELÉ ===

# O módulo relé normalmente funciona com:
# - Sinal HIGH (3.3V) = Relé LIGADO = Resistência LIGADA
# - Sinal LOW (0V) = Relé DESLIGADO = Resistência DESLIGADA
RELAY_ACTIVE_HIGH = True       # True se relé ativa com sinal alto

# Configurações do segundo canal do relé (opcional)
RELAY2_PIN = 19                # Segundo canal (se necessário)
RELAY2_ENABLED = False         # Ativar segundo canal 
