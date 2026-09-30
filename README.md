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

### Nozzle -> Eddy DUO 코일 중심 위치 (printer.cfg 기준)
- X: -36.5mm (`x_offset`)
- Y: -16mm (`y_offset`)
- Z: +2mm

### Eddy DUO 설정 기준 (USB 모드)
이 설정은 **BTT Eddy DUO를 USB로 연결**한 기준 → Eddy DUO 자체 RP2040 MCU + 코일 서미스터 사용 (BTT Eddy USB와 같은 구성)

| 항목 | Eddy DUO (USB, 현재) | Eddy Coil (툴보드 I2C) |
|---|---|---|
| `[mcu eddy]` | 필요 (`/dev/serial/by-id/usb-Klipper_rp2040_...`) | 삭제 |
| `[temperature_sensor btt_eddy_mcu]` | 사용 | 삭제 |
| `[probe_eddy_current btt_eddy]` `i2c_mcu` / `i2c_bus` | `eddy` / `i2c0f` | 툴보드 MCU 이름 / 툴보드 I2C 버스 |
| `[temperature_probe btt_eddy]` | 사용 (`eddy:gpio26`) | 삭제 (온도 보정 없음) |
| `EDDY_CALIBRATE_TEMP` (4단계) | 사용 | 사용 불가 |

**Z 홈**: Z 스위치 없이 Eddy DUO를 Z endstop으로 사용
- `[stepper_z] endstop_pin: probe:z_virtual_endstop`
- `[gcode_macro G28]` → X/Y 홈 후 `FORCE_MOVE`로 Z 10mm 올린 뒤 Z 홈 (`[force_move]` 필요)
- `[safe_z_home]` 로 베드 중앙에서 Z 홈

**캘리브레이션 순서** (`EDDY_CALIBRATE` 실행 시 콘솔에 절차 출력, Fluidd 매크로도 이 순서로 정렬)

| 단계 | 매크로 | 이후 |
|---|---|---|
| 1-1 | `EDDY_PREP_20` (노즐 20mm 위치) | |
| 1-2 | `EDDY_CALIBRATE_COIL` | `SAVE_CONFIG` + 재시작 |
| 2 | `EDDY_CALIBRATE_PROBE` (베드 중앙 종이 테스트) | `SAVE_CONFIG` |
| 3 | `EDDY_BED_MESH` (rapid_scan 메쉬) | `SAVE_CONFIG` |
| 4 | `EDDY_CALIBRATE_TEMP` (차가운 상태 종이 테스트 → 가열) | `SAVE_CONFIG` |

### DS18B20 챔버 온도 센서 (선택)
Pi GPIO22에 1-wire로 연결, 커스텀 Klipper 모듈 `ds18b20/ds18b20_sysfs.py` (`sensor_type: DS18B20_HOST`) 로 sysfs 에서 읽음

- CRC 오류, 85.000°C(전원 리셋 기본값 = 변환 실패) 읽기는 버림
- 읽기 오류가 나도 프린터를 멈추지 않고 마지막 값 유지 (Klipper 내장 `DS18B20` + host MCU 방식은 읽기 오류 시 shutdown 되어 사용 안 함)

**설치**
1. 1-wire 활성화 (`/boot/firmware/config.txt`) 후 재부팅
   ```
   dtoverlay=w1-gpio,gpiopin=22,pullup=1
   ```
2. `ls /sys/bus/w1/devices/` 로 `28-xxxxxxxxxxxx` 시리얼 확인 → `ds18b20/ds18b20.cfg` 의 `serial_no` 에 입력
3. 모듈 링크 후 Klipper 재시작
   ```bash
   ./ds18b20/install.sh   # ~/klipper/klippy/extras/ds18b20_sysfs.py 심볼릭 링크 생성
   ```

**비활성화**: `ds18b20/` 폴더 삭제 → `printer.cfg` 는 `[include ds18b20/*.cfg]` 와일드카드라 파일이 없어도 에러 없음

**문제 해결**: 85°C가 자주 나오면 변환 중 센서가 리셋되는 것 → VDD 연결부 접촉/전원 확인 (VDD-GND 사이 100nF 커패시터 권장)

### ADXL345
현재 센서 분리 상태 → 연결 안 된 채로 include 하면 Klipper가 시작되지 않으므로 `printer.cfg` 에서 `#[include adxl.cfg]` 주석 처리
