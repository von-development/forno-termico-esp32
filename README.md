# Forno de Tratamentos Térmicos com ESP32 e Termopar

Este projeto implementa um sistema de controle e monitoramento de temperatura para um forno de tratamentos térmicos utilizando ESP32 e sensor de temperatura tipo K (MAX6675).

## Componentes Principais

- ESP32 (Microcontrolador)
- Sensor de Temperatura MAX6675 (Termopar tipo K)
- Display OLED SSD1306
- Sistema de controle de temperatura

## Funcionalidades

- Leitura de temperatura em tempo real via termopar
- Interface de visualização com display OLED
- Registro de data e hora das medições
- Sistema de controle de temperatura

## Requisitos de Hardware

- ESP32
- Módulo MAX6675
- Display OLED SSD1306
- Fonte de alimentação adequada
- Componentes de potência para controle do forno

## Requisitos de Software

- MicroPython
- Bibliotecas necessárias:
  - SSD1306.py (para o display OLED)
  - Bibliotecas padrão do MicroPython (machine, time, utime)

## Conexões

### MAX6675
- CS (Chip Select): GPIO 23
- SO (Serial Output): GPIO 19
- SCK (Serial Clock): GPIO 5

## Instalação

1. Instale o MicroPython no ESP32
2. Transfira a biblioteca SSD1306.py para o ESP32
3. Faça as conexões conforme especificado
4. Carregue o código principal

## Uso

O sistema permite:
- Monitoramento contínuo da temperatura
- Visualização dos dados no display OLED
- Registro temporal das medições
- Controle automático da temperatura do forno

## Desenvolvimento

Projeto desenvolvido no âmbito da disciplina de Instrumentação Eletrotécnica Aplicada (IEA) 2022-2023, atualizado em 2024-2025.

## Autores

- H. Ribeiro (2024-2025)
- A. Borges (2022-2023)

## Licença

Este projeto é parte do trabalho acadêmico do IEA.