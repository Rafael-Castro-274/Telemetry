# ACC Shared Memory - Referência Completa de Offsets

> **Última atualização:** 2026-01-15  
> **Baseado em:** ACCSharedMemory.h oficial

---

## 📋 Índice

1. [Physics (acpmf_physics)](#1-physics-acpmf_physics)
2. [Graphics (acpmf_graphics)](#2-graphics-acpmf_graphics)
3. [Static (acpmf_static)](#3-static-acpmf_static)
4. [Enums e Estados](#4-enums-e-estados)
5. [Ordem das Rodas](#5-ordem-das-rodas)

---

## 1. Physics (acpmf_physics)

**Frequência:** ~333 Hz  
**Tamanho:** ~4096 bytes

### Campos Básicos

| Campo           | Tipo    | Offset | Descrição                           |
|-----------------|---------|--------|-------------------------------------|
| packetId        | int     | 0      | ID incremental para sincronização   |
| gas             | float   | 4      | Acelerador (0.0 - 1.0)             |
| brake           | float   | 8      | Freio (0.0 - 1.0)                  |
| fuel            | float   | 12     | Combustível restante (litros)      |
| gear            | int     | 16     | Marcha (-1=Ré, 0=Neutro, 1-8)      |
| rpms            | int     | 20     | RPM atual do motor                  |
| steerAngle      | float   | 24     | Ângulo do volante (graus)          |
| speedKmh        | float   | 28     | Velocidade (km/h)                  |

### Pneus (Arrays de 4 elementos: FL, FR, RL, RR)

| Campo               | Tipo       | Offset | Descrição                    |
|---------------------|------------|--------|------------------------------|
| wheelSlip[4]        | float[4]   | 32     | Deslizamento das rodas       |
| tyrePressure[4]     | float[4]   | 48     | Pressão dos pneus (PSI)      |
| tyreWear[4]         | float[4]   | 64     | Desgaste dos pneus (%)       |
| tyreCoreTemp[4]     | float[4]   | 80     | Temperatura núcleo (°C)      |
| suspensionTravel[4] | float[4]   | 96     | Curso da suspensão (mm)      |

### Assistências (int: 0=Desligado, 1=Ligado)

| Campo          | Tipo | Offset | Descrição           |
|----------------|------|--------|---------------------|
| tc             | int  | 112    | Controle de tração  |
| abs            | int  | 116    | ABS                 |
| pitLimiterOn   | int  | 120    | Limitador de pit    |
| drs            | int  | 124    | DRS                 |

### Dinâmica do Veículo

| Campo              | Tipo       | Offset | Descrição                    |
|--------------------|------------|--------|------------------------------|
| accG[3]            | float[3]   | 128    | Aceleração G (x, y, z)       |
| localVelocity[3]   | float[3]   | 140    | Velocidade local (m/s)       |
| carDamage[5]       | float[5]   | 152    | Dano do carro (%)            |

---

## 2. Graphics (acpmf_graphics)

**Frequência:** Por frame gráfico (~60 Hz)  
**Tamanho:** ~4096 bytes

### Estado da Sessão

| Campo           | Tipo    | Offset | Descrição                              |
|-----------------|---------|--------|----------------------------------------|
| packetId        | int     | 0      | ID incremental                         |
| status          | int     | 4      | 0=OFF, 1=REPLAY, 2=LIVE               |
| session         | int     | 8      | 0=Prática, 1=Quali, 2=Corrida         |
| currentTime     | wchar   | 12     | Tempo atual (string)                   |
| lastTime        | wchar   | 76     | Último tempo de volta (string)         |
| bestTime        | wchar   | 140    | Melhor tempo de volta (string)         |
| split           | wchar   | 204    | Split time (string)                    |

### Corrida

| Campo             | Tipo    | Offset | Descrição                          |
|-------------------|---------|--------|------------------------------------|
| completedLaps     | int     | 268    | Voltas completas                   |
| position          | int     | 272    | Posição atual na corrida           |
| iCurrentTime      | int     | 276    | Tempo atual (ms)                   |
| iLastTime         | int     | 280    | Último tempo de volta (ms)         |
| iBestTime         | int     | 284    | Melhor tempo de volta (ms)         |
| sessionTimeLeft   | float   | 288    | Tempo restante de sessão (ms)      |
| distanceTraveled  | float   | 292    | Distância percorrida (m)           |
| isInPit           | int     | 296    | 0=Pista, 1=Pit                     |
| currentSectorIndex| int     | 300    | Setor atual (0, 1, 2)              |
| lastSectorTime    | int     | 304    | Tempo do último setor (ms)         |
| numberOfLaps      | int     | 308    | Número total de voltas             |

### Condições e Bandeiras

| Campo                  | Tipo    | Offset | Descrição                      |
|------------------------|---------|--------|--------------------------------|
| tyreCompound           | wchar   | 312    | Composto do pneu (string)      |
| replayTimeMultiplier   | float   | 376    | Multiplicador de replay        |
| normalizedCarPosition  | float   | 380    | Posição na pista (0.0-1.0)     |
| activeCars             | int     | 384    | Carros ativos na sessão        |
| carCoordinates[60][3]  | float   | 388    | Coordenadas X,Y,Z de 60 carros |
| carID[60]              | int     | 1108   | IDs dos carros                 |
| playerCarID            | int     | 1348   | ID do carro do jogador         |
| penaltyTime            | float   | 1352   | Tempo de penalidade (s)        |
| flag                   | int     | 1356   | Bandeira atual (enum)          |
| idealLineOn            | int     | 1360   | Linha ideal ativa              |

### Eletrônicos (Rain Light, etc)

| Campo           | Tipo | Offset | Descrição                    |
|-----------------|------|--------|------------------------------|
| rainLights      | int  | 1364   | Luzes de chuva               |
| flashingLights  | int  | 1368   | Luzes piscando               |
| lightsStage     | int  | 1372   | Estágio dos faróis           |
| exhaustTemp     | float| 1376   | Temperatura do escapamento   |
| wiperLV         | int  | 1380   | Nível do limpador            |

### Condições Climáticas (Graphics!)

| Campo           | Tipo  | Offset | Descrição                    |
|-----------------|-------|--------|------------------------------|
| airTemp         | float | 1384   | Temperatura do ar (°C)       |
| roadTemp        | float | 1388   | Temperatura da pista (°C)    |
| rainIntensity   | float | 1392   | Intensidade da chuva (0-1)   |

---

## 3. Static (acpmf_static)

**Frequência:** Uma vez por sessão  
**Tamanho:** ~4096 bytes

### Informações do Veículo

| Campo              | Tipo      | Offset | Descrição                       |
|--------------------|-----------|--------|---------------------------------|
| smVersion          | wchar[15] | 0      | Versão do Shared Memory         |
| acVersion          | wchar[15] | 30     | Versão do ACC                   |
| numberOfSessions   | int       | 60     | Número de sessões               |
| numCars            | int       | 64     | Número de carros                |
| carModel           | wchar[33] | 68     | Modelo do carro                 |
| track              | wchar[33] | 134    | Nome da pista                   |
| playerName         | wchar[33] | 200    | Nome do piloto                  |
| playerSurname      | wchar[33] | 266    | Sobrenome do piloto             |
| playerNick         | wchar[33] | 332    | Nick do piloto                  |

### Especificações Técnicas

| Campo              | Tipo | Offset | Descrição                    |
|--------------------|------|--------|------------------------------|
| sectorCount        | int  | 398    | Número de setores            |
| maxTorque          | float| 402    | Torque máximo (Nm)           |
| maxPower           | float| 406    | Potência máxima (W)          |
| maxRpm             | int  | 410    | RPM máximo                   |
| maxFuel            | float| 414    | Capacidade de combustível    |
| suspensionMaxTravel[4] | float[4] | 418 | Curso máx suspensão     |
| tyreRadius[4]      | float[4] | 434 | Raio dos pneus (m)          |
| maxTurboBoost      | float| 450    | Boost máximo turbo           |

### Penalidades e Assistências

| Campo              | Tipo | Offset | Descrição                    |
|--------------------|------|--------|------------------------------|
| penaltiesEnabled   | int  | 454    | Penalidades habilitadas      |
| aidFuelRate        | float| 458    | Taxa de consumo (aid)        |
| aidTireRate        | float| 462    | Taxa de desgaste (aid)       |
| aidMechanicalDamage| float| 466    | Dano mecânico (aid)          |
| aidAllowTyreBlankets| int | 470    | Aquecedores permitidos       |
| aidStability       | float| 474    | Auxílio de estabilidade      |
| aidAutoClutch      | int  | 478    | Embreagem automática         |
| aidAutoBlip        | int  | 482    | Auto blip                    |

---

## 4. Enums e Estados

### AC_STATUS (Graphics.status)

```c
AC_OFF = 0      // ACC fechado ou no menu
AC_REPLAY = 1   // Modo replay
AC_LIVE = 2     // Sessão ativa
```

### AC_SESSION_TYPE (Graphics.session)

```c
AC_UNKNOWN = -1
AC_PRACTICE = 0
AC_QUALIFY = 1
AC_RACE = 2
AC_HOTLAP = 3
AC_TIME_ATTACK = 4
AC_DRIFT = 5
AC_DRAG = 6
AC_HOTSTINT = 7
AC_HOTSTINT_SUPERPOLE = 8
```

### AC_FLAG_TYPE (Graphics.flag)

```c
AC_NO_FLAG = 0
AC_BLUE_FLAG = 1
AC_YELLOW_FLAG = 2
AC_BLACK_FLAG = 3
AC_WHITE_FLAG = 4
AC_CHECKERED_FLAG = 5
AC_PENALTY_FLAG = 6
```

---

## 5. Ordem das Rodas

Todos os arrays de 4 elementos seguem esta ordem:

```
[0] = Front Left  (FL)
[1] = Front Right (FR)
[2] = Rear Left   (RL)
[3] = Rear Right  (RR)
```

---

## 📝 Notas Importantes

1. **wchar strings:** Ocupam 2 bytes por caractere (UTF-16). Para ler:
   ```python
   raw = mm.read(length * 2)
   text = raw.decode("utf-16", errors="ignore").split("\x00")[0]
   ```

2. **Temperaturas:** airTemp e roadTemp estão em **Graphics**, não Static!

3. **Sincronização:** Use `packetId` para detectar atualizações

4. **Validação:** Sempre verificar `Graphics.status == 2` (AC_LIVE) antes de processar dados

5. **Arrays:** Acessar com cuidado, calculando offset correto:
   ```
   offset_wheel_0 = base_offset + (0 * 4)  // float = 4 bytes
   offset_wheel_1 = base_offset + (1 * 4)
   ```

---

## 🔗 Referências

- Arquivo oficial: `ACCSharedMemory.h`
- Documentação: SDK do ACC
- Comunidade: ACC Forums

---

**Projeto:** Corredor X - Telemetria ACC  
**Versão:** 2.0  
**Autor:** Rafael Castro
