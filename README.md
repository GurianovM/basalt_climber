# Шестилапый скалолаз «Базальт»

Реализация модели `BasaltClimber` по предоставленному `SPEC.md` и набору `TEST_CASES.md` версии 0.2.

## Требования

- Python 3.10 или новее.
- Внешние пакеты не требуются: используются только стандартная библиотека Python и `unittest`.

## Структура проекта

```text
basalt_climber/
├── basalt_climber.py
├── SPEC.md
├── TEST_CASES.md
├── CHANGELOG.md
├── README.md
├── BUGREPORT.md
└── tests/
    └── test_basalt_climber.py
```

## Запуск тестов

Команды выполняются из корневой папки проекта:

```bash
python -m unittest discover -s tests -v
```

В Windows также можно использовать `py -3` вместо `python`:

```powershell
py -3 -m unittest discover -s tests -v
```

Ожидаемый результат текущего прогона: **35 тестов успешно, ошибок нет**.

## Использование

```python
from basalt_climber import BasaltClimber, BasaltNoStrength

basalt = BasaltClimber(
    "Базальт",
    mass_kg=300,
    max_speed_kmh=12,
)

hours = basalt.move(6, "rock")
print(f"Время перемещения: {hours:.2f} ч")
print(basalt.get_status())

try:
    basalt.move(100, "cliff")
except BasaltNoStrength as error:
    print(error)
    print(error.required, error.available)
```

## Реализованный интерфейс

- `BasaltClimber(...)` — создание аппарата с проверкой типов, диапазонов и конечности числовых значений.
- `move(distance_km, terrain)` — движение по камню, песку или скале; вода запрещена.
- `can_overcome(obstacle)` — проверка препятствия без изменения состояния.
- `calculate_energy(distance_km, terrain)` — расчёт расхода без изменения состояния и без проверки возможности фактического движения.
- `refuel(amount)` — пополнение энергии до максимума 100.
- `damage_leg()` и `repair_legs()` — повреждение одной лапы и восстановление всех лап.
- `get_status()` — независимый словарь с состоянием аппарата.

Публичные атрибуты доступны только для чтения. При ошибке метода состояние не изменяется. Доменные исключения `BasaltError` наследуются от `CrazyVehicleError`; у `BasaltNoStrength` доступны атрибуты `required` и `available`.

## Примечание по версии ТЗ

В переданном файле `SPEC.md` в заголовке указана версия 0.1, тогда как `TEST_CASES.md` ссылается на `SPEC.md` v0.2, а `CHANGELOG.md` описывает изменения версии 0.2. Несоответствие зафиксировано в `BUGREPORT.md`; файл ТЗ разработчиком не изменялся.
