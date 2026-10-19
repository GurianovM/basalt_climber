# Test Case Specification: Шестилапый скалолаз «Базальт»

Версия: 0.1 (к SPEC.md v0.1)

Эталонный аппарат (если не сказано иное): `BasaltClimber("Базальт", mass_kg=300, max_speed_kmh=12, energy=100)`. Шесть исправных лап, грузоподъёмность сцепления 360 кг.

Соотношение: 29 модульных / 5 сценарных ≈ 85 / 15.

## Модульные тесты (module, AAA)

| ID | Тип | Источник | Предусловие | Вход | Ожидание | Приоритет |
|---|---|---|---|---|---|---|
| TC-01 | module | SPEC 3.2, 3.3 | — | эталон, energy не передана, mass_kg=300 (int), max_speed_kmh=12 (int) | атрибуты равны входу; energy=100.0; position_km=0.0; is_climbing=False; leg_count=6; working_legs=6; grip_capacity_kg=360.0; can_walk=True; can_climb=True; mass_kg, max_speed_kmh, energy, position_km, grip_capacity_kg типа float; leg_count и working_legs типа int | high |
| TC-02 | module | SPEC 3.2 | — | name="" ; name="   " | ValueError | high |
| TC-03 | module | SPEC 3.2 | — | mass_kg, max_speed_kmh = 0 и -1 | ValueError | high |
| TC-04 | module | SPEC 3.2, 5 | — | energy=-0.1 ; energy=100.1 ; energy=0 ; energy=100 | -0.1 и 100.1 → ValueError; 0 и 100 → объект создан | high |
| TC-05 | module | SPEC 3.0, 3.2 | — | name=123 ; name=None ; mass_kg="300" ; mass_kg=True ; max_speed_kmh=None ; energy="50" | TypeError | medium |
| TC-06 | module | SPEC 3.3 | эталон | присвоение любого публичного атрибута | AttributeError | medium |
| TC-07 | module | SPEC 3.4.1 | эталон | move(6, "rock") | вернул 0.5; energy=94; position_km=6; is_climbing=False | high |
| TC-08 | module | SPEC 3.4.1 | эталон | move(3, "sand") | вернул 0.5 (скорость 6 км/ч); energy=94 (расход 2 ед./км); position_km=3; is_climbing=False | high |
| TC-09 | module | SPEC 3.4.1 | эталон | move(1.5, "cliff") | вернул 0.5 (скорость 3 км/ч); energy=94 (расход 4 ед./км); position_km=1.5; is_climbing=True | high |
| TC-10 | module | SPEC 3.4.1 | после move(1.5, "cliff"): energy=94, position=1.5, is_climbing=True | а) move(1.5, "rock"); б) move(3, "sand") | а) вернул 0.125; energy=92.5; position_km=3; is_climbing=False; б) вернул 0.5; energy=88; position_km=4.5; is_climbing=False | high |
| TC-11 | module | SPEC 3.4.1 | эталон; отдельно эталон на скале | move(1, "water") | BasaltCannotSwim; состояние не изменилось (и на земле, и на скале) | high |
| TC-12 | module | SPEC 3.4.1 | эталон | move(0, "rock") ; move(-5, "rock") ; move(1, "air") ; move(1, "") | ValueError; состояние не изменилось | high |
| TC-13 | module | SPEC 3.0, 3.4.1 | эталон | move("10", "rock") ; move(True, "rock") ; move(None, "rock") ; move(1, 1) | TypeError | medium |
| TC-14 | module | SPEC 3.0, 3.4.1 | energy=10 | move(5, "cliff") | BasaltNoStrength, required=20, available=10; energy=10; position_km=0; is_climbing=False; working_legs=6 | high |
| TC-15 | module | SPEC 3.4.1, 5 | energy=100 | move(25, "cliff") | вернул 8.333333; energy=0.0; position_km=25; is_climbing=True | high |
| TC-16 | module | SPEC 2, 3.3, 3.4.1, 5 | а) mass_kg=400, 6 лап; б) mass_kg=360, 6 лап; в) mass_kg=300, 5 лап (одна лапа повреждена); г) mass_kg=300, 4 лапы | move(1, "cliff"); для а) также move(1, "rock") | а) grip_capacity=360, can_climb=False, BasaltGripFailure, состояние не изменилось, по камню идёт (вернул 0.083333); б) can_climb=True, подъём успешен; в) grip_capacity=300 (масса равна), can_climb=True, подъём успешен; г) grip_capacity=240, can_climb=False, BasaltGripFailure | high |
| TC-17 | module | SPEC 2, 3.4.1, 5 | mass_kg=100; а) 3 исправные лапы; б) 2 исправные лапы | move(1, "rock") ; move(1, "sand") ; move(1, "cliff") | а) can_walk=True, can_climb=True, все три перемещения успешны; б) can_walk=False, все три → BasaltLegsDamaged, состояние не изменилось | high |
| TC-18 | module | SPEC 6.3 | несколько нарушений одновременно | см. колонку «Ожидание» | 2 лапы + energy=0, "rock" → BasaltLegsDamaged; 2 лапы + mass=400, "cliff" → BasaltLegsDamaged; mass=400 + energy=0, "cliff" → BasaltGripFailure; 6 лап, mass=300, energy=0, "rock" → BasaltNoStrength; 2 лапы, "water" → BasaltCannotSwim; energy=0, "water" → BasaltCannotSwim; move(0, "water") → ValueError; move("1", "space") → TypeError | medium |
| TC-19 | module | SPEC 3.4.3 | эталон; отдельно energy=10; отдельно 2 лапы; отдельно mass_kg=400 | calculate_energy(10, "rock") ; (10, "sand") ; (10, "cliff") ; (1000, "cliff") при energy=10 ; (10, "rock") при 2 лапах ; (10, "cliff") при mass=400 | 10 ; 20 ; 40 ; 4000 без исключения ; 10 без исключения ; 40 без исключения; состояние не изменилось | high |
| TC-20 | module | SPEC 3.4.3 | эталон | calculate_energy(1, "water") ; (0, "rock") ; (1, "air") ; ("1", "rock") | BasaltCannotSwim ; ValueError ; ValueError ; TypeError | medium |
| TC-21 | module | SPEC 3.4.2 | 8 состояний: стоит на земле; на скале; mass=400 на земле; 4 лапы при mass=300; 3 лапы при mass=100; energy=0 на земле; energy=0 на скале (после move(25, "cliff")); 2 лапы | can_overcome("wall" / "river" / "boulder") | на земле: T / F / T; на скале: T / F / T; mass=400: F / F / T; 4 лапы: F / F / T; 3 лапы, mass=100: T / F / F; energy=0 на земле: F / F / F; energy=0 на скале: T / F / F; 2 лапы: F / F / F; состояние не изменилось | high |
| TC-22 | module | SPEC 3.4.2 | эталон | can_overcome("mountain") ; ("") ; (42) ; (None) | ValueError ; ValueError ; TypeError ; TypeError | medium |
| TC-23 | module | SPEC 3.4.4, 5 | energy=20 ; energy=50 ; energy=100 | refuel(50) ; refuel(1000) ; refuel(0.5) | 70 ; 100 ; 100; метод возвращает None | high |
| TC-24 | module | SPEC 3.4.4 | energy=50 | refuel(0) ; (-5) ; ("10") ; (True) | ValueError ; ValueError ; TypeError ; TypeError; energy=50 | medium |
| TC-25 | module | SPEC 3.4.5 | а) эталон после move(2, "cliff"): energy=92; б) эталон на земле; в) mass_kg=100 после move(1, "cliff") | damage_leg() (несколько раз) | а) 1-й вызов: working_legs=5, grip_capacity=300, остаётся на скале (can_climb=True); 2-й вызов: working_legs=4, grip_capacity=240, срыв: is_climbing=False, can_climb=False; energy=92, position_km=2; б) working_legs=5, position_km и energy не изменились; в) при 3 лапах остаётся на скале; при 2 лапах срыв (хотя 120 ≥ 100), is_climbing=False | high |
| TC-26 | module | SPEC 3.4.5, 5 | эталон | damage_leg() 7 раз подряд | working_legs=0 и остаётся 0, без исключений; grip_capacity_kg=0.0; can_walk=False; can_climb=False | medium |
| TC-27 | module | SPEC 3.4.6 | а) 4 лапы повреждены частично (working_legs=3), на земле; б) лапы исправны; в) исправные лапы, на скале | repair_legs() | а) working_legs=6, grip_capacity=360, can_climb=True, is_climbing=False; б) без ошибок, working_legs=6; в) is_climbing остаётся True; energy и position_km не меняются | high |
| TC-28 | module | SPEC 3.4.7 | после move(10, "rock") | get_status(), затем изменить словарь | ключи ровно {name, energy, position_km, is_climbing, working_legs, can_walk, can_climb}; значения "Базальт", 90, 10, False, 6, True, True; working_legs типа int; изменение словаря не меняет объект | medium |
| TC-29 | module | SPEC 6.1 | — | issubclass(...) | 4 доменных ⊂ BasaltError ⊂ CrazyVehicleError ⊂ Exception; BasaltNoStrength имеет required/available | medium |

## Сценарные тесты (scenario, GWT)

| ID | Тип | Источник | Вход | Ожидание | Приоритет |
|---|---|---|---|---|---|
| TC-30 | scenario | SPEC 4.2, сц. 5 | все шаги «Доставка груза в горный приют» | position_km=28; energy=60; is_climbing=True; промежуточные BasaltCannotSwim и BasaltNoStrength(80, 74.5) | high |
| TC-31 | scenario | SPEC 4.2, сц. 6 | все шаги «Обвал на карнизе» | position_km=7; energy=81; is_climbing=True; working_legs=6; промежуточные BasaltGripFailure и BasaltLegsDamaged | high |
| TC-32 | scenario | SPEC 4.2, сц. 7 | все шаги «Тяжеловес у реки» | position_km=60; energy=100; is_climbing=False; can_climb=False; промежуточные BasaltGripFailure, BasaltCannotSwim, BasaltNoStrength(1, 0) | high |
| TC-33 | scenario | SPEC 4.2, сц. 8 | все шаги «Последний рывок на скале» | position_km=26; energy=0; is_climbing=True | medium |
| TC-34 | scenario | SPEC 4.2, сц. 9 | все шаги «Впритык по сцеплению» | position_km=20; energy=0; is_climbing=False; working_legs=6; can_climb=False | medium |