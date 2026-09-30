# Ender V3 SE Klipper Config
> with Eddy DUO + a(soon)

### 3D Models & Modding

#### Models
- [Eddy Mount](https://www.printables.com/model/1402895-ender-3-v3-se-btt-eddy-mount)
- [5020 fan duct](https://www.printables.com/model/778630-ender-3-v3-se-5020-fan-duct)
- [4020 hotend fan mount](https://www.printables.com/model/1270498-ender-3-v3-se-wceramic-hotend-upgrade-4010-4020-fa) 
- [BentoBox/WIP](https://www.printables.com/model/272525-bentobox-v20-carbon-filter-for-bambu-lab-x1c-enclo)
- (Soon) Ender V3 SE XYZ Stepper Motor Fan Mount

#### Modding
- RDBB MGN 9H 300mm x3
- MGN 9H X/Y axis upgrade (Aliexpress)
- Ceramic Hotend
- Eddy DUO(USB)
- GDSTIME 5020 fan (nozzle cooling)
- WINSIN 4020 fan (hotend cooling)

> Eddy Mount 상단부를 적절히 잘라야 함
> 4020 hotend fan mount 는 간섭이 있어 102% 출력 권장

### Nozzle -> Eddy DUO 물리적 위치
- X: -34mm
- Y: +16mm
- Z: +2mm

### DS18B20 온도 센서 (Pi host MCU)
Pi GPIO22에 1-wire로 연결, Klipper 내장 `DS18B20` 센서를 Linux host MCU(`[mcu host]`)로 읽음

1. 1-wire 활성화 (`/boot/firmware/config.txt`) 후 재부팅
   ```
   dtoverlay=w1-gpio,gpiopin=22,pullup=1
   ```
   `ls /sys/bus/w1/devices/` 로 `28-xxxxxxxxxxxx` 시리얼 확인 → `printer.cfg` 의 `serial_no` 에 입력
2. Host MCU 빌드/설치 (메인보드용 `.config`, `out/` 과 분리)
   ```bash
   cd ~/klipper
   sudo cp ./scripts/klipper-mcu.service /etc/systemd/system/
   sudo systemctl enable klipper-mcu.service
   make KCONFIG_CONFIG=.config.host OUT=out_host/ menuconfig   # Micro-controller Architecture: Linux process
   sudo systemctl stop klipper
   make KCONFIG_CONFIG=.config.host OUT=out_host/ flash
   sudo systemctl start klipper-mcu klipper
   ```
3. `printer.cfg` 의 `[mcu host]`, `[temperature_sensor ds18b20]` 사용

> 이전에 쓰던 커스텀 모듈 `klippy/extras/ds18b20_sysfs.py` (`DS18B20_HOST`) 는 더 이상 필요 없음

### ADXL345
현재 센서 분리 상태 → 연결 안 된 채로 include 하면 Klipper가 시작되지 않으므로 `printer.cfg` 에서 `#[include adxl.cfg]` 주석 처리
