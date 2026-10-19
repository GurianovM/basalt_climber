"""Тесты для шестилапого скалолаза «Базальт» (SPEC.md v0.1, TEST_CASES.md v0.1).

Запуск из корня репозитория:
    python -m unittest discover -s tests -v
Модульные тесты построены по паттерну AAA (Arrange-Act-Assert),
сценарные — по Given-When-Then через тестовые обёртки Pilot, Rockfall и Workshop.
Каждый тест содержит ID своего тест-кейса в имени и в docstring.
"""

import unittest

from basalt_climber import (
    BasaltCannotSwim,
    BasaltClimber,
    BasaltError,
    BasaltGripFailure,
    BasaltLegsDamaged,
    BasaltNoStrength,
    CrazyVehicleError,
)

PLACES = 6


def make_basalt(**overrides):
    """Эталонный аппарат из SPEC 4: 300 кг, 12 км/ч, энергия 100, 6 лап."""
    params = {
        "name": "Базальт",
        "mass_kg": 300.0,
        "max_speed_kmh": 12.0,
        "energy": 100.0,
    }
    params.update(overrides)
    return BasaltClimber(**params)


def damage(basalt, times):
    """Вывести из строя несколько лап подряд."""
    for _ in range(times):
        basalt.damage_leg()


def snapshot(basalt):
    """Наблюдаемое состояние аппарата для проверки атомарности."""
    return (
        basalt.energy,
        basalt.position_km,
        basalt.is_climbing,
        basalt.working_legs,
    )


# Сценарии


class Pilot:
    """Эмулятор пилота: управляет аппаратом на доменном языке."""

    def __init__(self, basalt):
        self._basalt = basalt

    def идти_по_камням(self, distance_km):
        return self._basalt.move(distance_km, "rock")

    def идти_по_песку(self, distance_km):
        return self._basalt.move(distance_km, "sand")

    def лезть_на_скалу(self, distance_km):
        return self._basalt.move(distance_km, "cliff")

    def спуститься(self, distance_km):
        return self._basalt.move(distance_km, "rock")

    def переплыть(self, distance_km):
        return self._basalt.move(distance_km, "water")

    def может_преодолеть(self, obstacle):
        return self._basalt.can_overcome(obstacle)

    def подзарядиться(self, amount):
        self._basalt.refuel(amount)


class Rockfall:
    """Обвал: выводит из строя одну лапу."""

    def обрушить(self, basalt):
        basalt.damage_leg()


class Workshop:
    """Мастерская: восстанавливает все лапы."""

    def починить_лапы(self, basalt):
        basalt.repair_legs()


# Модульные тесты (AAA)


class TestConstructor(unittest.TestCase):
    """SPEC 3.2, 3.3."""

    def test_tc01_init_valid_defaults(self):
        """TC-01. Корректное создание и начальное состояние."""
        basalt = BasaltClimber("Базальт", mass_kg=300, max_speed_kmh=12)

        self.assertEqual(basalt.name, "Базальт")
        self.assertAlmostEqual(basalt.mass_kg, 300.0, places=PLACES)
        self.assertAlmostEqual(basalt.max_speed_kmh, 12.0, places=PLACES)
        self.assertAlmostEqual(basalt.energy, 100.0, places=PLACES)
        self.assertAlmostEqual(basalt.position_km, 0.0, places=PLACES)
        self.assertIs(basalt.is_climbing, False)
        self.assertEqual(basalt.leg_count, 6)
        self.assertEqual(basalt.working_legs, 6)
        self.assertAlmostEqual(basalt.grip_capacity_kg, 360.0, places=PLACES)
        self.assertIs(basalt.can_walk, True)
        self.assertIs(basalt.can_climb, True)
        for attr in ("mass_kg", "max_speed_kmh", "energy",
                     "position_km", "grip_capacity_kg"):
            with self.subTest(attr=attr):
                self.assertIsInstance(getattr(basalt, attr), float)
        for attr in ("leg_count", "working_legs"):
            with self.subTest(attr=attr):
                self.assertIsInstance(getattr(basalt, attr), int)

    def test_tc02_init_empty_name_raises(self):
        """TC-02. Пустое имя или имя из пробелов → ValueError."""
        for bad_name in ("", "   "):
            with self.subTest(name=bad_name):
                # Act / Assert
                with self.assertRaises(ValueError):
                    make_basalt(name=bad_name)

    def test_tc03_init_non_positive_values_raise(self):
        """TC-03. Масса и скорость ≤ 0 → ValueError."""
        for param in ("mass_kg", "max_speed_kmh"):
            for value in (0, -1):
                with self.subTest(param=param, value=value):
                    with self.assertRaises(ValueError):
                        make_basalt(**{param: value})

    def test_tc04_init_energy_range(self):
        """TC-04. Энергия вне 0…100 → ValueError; границы 0 и 100 допустимы."""
        for bad_energy in (-0.1, 100.1):
            with self.subTest(energy=bad_energy):
                with self.assertRaises(ValueError):
                    make_basalt(energy=bad_energy)

        for ok_energy in (0, 100):
            with self.subTest(energy=ok_energy):
                basalt = make_basalt(energy=ok_energy)
                self.assertAlmostEqual(basalt.energy, float(ok_energy),
                                       places=PLACES)

    def test_tc05_init_wrong_types_raise(self):
        """TC-05. Неверные типы параметров конструктора → TypeError."""
        cases = [
            {"name": 123},
            {"name": None},
            {"mass_kg": "300"},
            {"mass_kg": True},
            {"max_speed_kmh": None},
            {"energy": "50"},
        ]
        for overrides in cases:
            with self.subTest(overrides=overrides):
                with self.assertRaises(TypeError):
                    make_basalt(**overrides)

    def test_tc06_attributes_read_only(self):
        """TC-06. Публичные атрибуты доступны только для чтения."""
        basalt = make_basalt()
        assignments = [
            ("name", "Другой"),
            ("mass_kg", 1.0),
            ("max_speed_kmh", 1.0),
            ("energy", 50.0),
            ("position_km", 5.0),
            ("is_climbing", True),
            ("leg_count", 4),
            ("working_legs", 3),
            ("grip_capacity_kg", 1.0),
            ("can_walk", False),
            ("can_climb", False),
        ]
        for attr, value in assignments:
            with self.subTest(attr=attr):
                with self.assertRaises(AttributeError):
                    setattr(basalt, attr, value)


class TestMove(unittest.TestCase):
    """SPEC 3.4.1, 6.3."""

    def test_tc07_move_rock(self):
        """TC-07. Камень: скорость max_speed, расход 1 ед./км."""
        basalt = make_basalt()

        hours = basalt.move(6, "rock")

        self.assertAlmostEqual(hours, 0.5, places=PLACES)
        self.assertAlmostEqual(basalt.energy, 94.0, places=PLACES)
        self.assertAlmostEqual(basalt.position_km, 6.0, places=PLACES)
        self.assertIs(basalt.is_climbing, False)

    def test_tc08_move_sand(self):
        """TC-08. Песок: скорость ×0.5, расход 2 ед./км."""
        basalt = make_basalt()

        hours = basalt.move(3, "sand")

        self.assertAlmostEqual(hours, 0.5, places=PLACES)
        self.assertAlmostEqual(basalt.energy, 94.0, places=PLACES)
        self.assertAlmostEqual(basalt.position_km, 3.0, places=PLACES)
        self.assertIs(basalt.is_climbing, False)

    def test_tc09_move_cliff(self):
        """TC-09. Скала: скорость ×0.25, расход 4 ед./км, is_climbing."""
        basalt = make_basalt()

        hours = basalt.move(1.5, "cliff")

        self.assertAlmostEqual(hours, 0.5, places=PLACES)
        self.assertAlmostEqual(basalt.energy, 94.0, places=PLACES)
        self.assertAlmostEqual(basalt.position_km, 1.5, places=PLACES)
        self.assertIs(basalt.is_climbing, True)

    def test_tc10_descend_from_cliff(self):
        """TC-10. Спуск: move по камню или песку со скалы снимает is_climbing."""
        with self.subTest(case="спуск по камню"):
            basalt = make_basalt()
            basalt.move(1.5, "cliff")

            hours = basalt.move(1.5, "rock")

            self.assertAlmostEqual(hours, 0.125, places=PLACES)
            self.assertAlmostEqual(basalt.energy, 92.5, places=PLACES)
            self.assertAlmostEqual(basalt.position_km, 3.0, places=PLACES)
            self.assertIs(basalt.is_climbing, False)

        with self.subTest(case="спуск на песок"):
            basalt = make_basalt()
            basalt.move(1.5, "cliff")

            hours = basalt.move(3, "sand")

            self.assertAlmostEqual(hours, 0.5, places=PLACES)
            self.assertAlmostEqual(basalt.energy, 88.0, places=PLACES)
            self.assertAlmostEqual(basalt.position_km, 4.5, places=PLACES)
            self.assertIs(basalt.is_climbing, False)

    def test_tc11_move_water_raises_cannot_swim(self):
        """TC-11. Вода → BasaltCannotSwim, состояние не меняется."""
        with self.subTest(case="на земле"):
            basalt = make_basalt()
            before = snapshot(basalt)

            with self.assertRaises(BasaltCannotSwim):
                basalt.move(1, "water")
            self.assertEqual(snapshot(basalt), before)

        with self.subTest(case="на скале"):
            basalt = make_basalt()
            basalt.move(1, "cliff")
            before = snapshot(basalt)
            with self.assertRaises(BasaltCannotSwim):
                basalt.move(1, "water")
            self.assertEqual(snapshot(basalt), before)

    def test_tc12_move_invalid_values_raise(self):
        """TC-12. Дистанция ≤ 0 или неизвестная поверхность → ValueError."""
        basalt = make_basalt()
        before = snapshot(basalt)

        for args in ((0, "rock"), (-5, "rock"), (1, "air"), (1, "")):
            with self.subTest(args=args):
                with self.assertRaises(ValueError):
                    basalt.move(*args)
        self.assertEqual(snapshot(basalt), before)

    def test_tc13_move_wrong_types_raise(self):
        """TC-13. Неверные типы аргументов move → TypeError."""
        basalt = make_basalt()

        for args in (("10", "rock"), (True, "rock"), (None, "rock"), (1, 1)):
            with self.subTest(args=args):
                with self.assertRaises(TypeError):
                    basalt.move(*args)

    def test_tc14_move_no_strength(self):
        """TC-14. Нехватка энергии → BasaltNoStrength, состояние не меняется."""
        basalt = make_basalt(energy=10)
        before = snapshot(basalt)

        with self.assertRaises(BasaltNoStrength) as ctx:
            basalt.move(5, "cliff")

        self.assertAlmostEqual(ctx.exception.required, 20.0, places=PLACES)
        self.assertAlmostEqual(ctx.exception.available, 10.0, places=PLACES)
        self.assertEqual(snapshot(basalt), before)

    def test_tc15_move_spends_all_energy_exactly(self):
        """TC-15. Расход ровно равен запасу — перемещение разрешено."""
        basalt = make_basalt(energy=100)

        hours = basalt.move(25, "cliff")

        self.assertAlmostEqual(hours, 25 / 3, places=PLACES)
        self.assertAlmostEqual(basalt.energy, 0.0, places=PLACES)
        self.assertAlmostEqual(basalt.position_km, 25.0, places=PLACES)
        self.assertIs(basalt.is_climbing, True)

    def test_tc16_grip_capacity_boundary(self):
        """TC-16. Сцепление: превышение запрещает подъём, равенство — нет."""
        with self.subTest(case="масса 400 кг, 6 лап"):
            heavy = make_basalt(mass_kg=400)
            before = snapshot(heavy)

            self.assertAlmostEqual(heavy.grip_capacity_kg, 360.0,
                                   places=PLACES)
            self.assertIs(heavy.can_climb, False)
            with self.assertRaises(BasaltGripFailure):
                heavy.move(1, "cliff")
            self.assertEqual(snapshot(heavy), before)
            self.assertAlmostEqual(heavy.move(1, "rock"), 1 / 12,
                                   places=PLACES)

        with self.subTest(case="масса 360 кг, 6 лап (равенство)"):
            exact = make_basalt(mass_kg=360)

            exact.move(1, "cliff")

            self.assertIs(exact.can_climb, True)
            self.assertIs(exact.is_climbing, True)

        with self.subTest(case="масса 300 кг, 5 лап (равенство)"):
            basalt = make_basalt(mass_kg=300)
            basalt.damage_leg()

            basalt.move(1, "cliff")

            self.assertAlmostEqual(basalt.grip_capacity_kg, 300.0,
                                   places=PLACES)
            self.assertIs(basalt.can_climb, True)
            self.assertIs(basalt.is_climbing, True)

        with self.subTest(case="масса 300 кг, 4 лапы"):
            basalt = make_basalt(mass_kg=300)
            damage(basalt, 2)
            before = snapshot(basalt)

            self.assertAlmostEqual(basalt.grip_capacity_kg, 240.0,
                                   places=PLACES)
            self.assertIs(basalt.can_climb, False)
            with self.assertRaises(BasaltGripFailure):
                basalt.move(1, "cliff")
            self.assertEqual(snapshot(basalt), before)

    def test_tc17_legs_damaged_threshold(self):
        """TC-17. Минимум трёх исправных лап для движения."""
        with self.subTest(case="3 исправные лапы"):
            basalt = make_basalt(mass_kg=100)
            damage(basalt, 3)

            self.assertEqual(basalt.working_legs, 3)
            self.assertIs(basalt.can_walk, True)
            self.assertIs(basalt.can_climb, True)
            basalt.move(1, "rock")
            basalt.move(1, "sand")
            basalt.move(1, "cliff")
            self.assertIs(basalt.is_climbing, True)
            self.assertAlmostEqual(basalt.position_km, 3.0, places=PLACES)

        with self.subTest(case="2 исправные лапы"):
            basalt = make_basalt(mass_kg=100)
            damage(basalt, 4)
            before = snapshot(basalt)

            self.assertEqual(basalt.working_legs, 2)
            self.assertIs(basalt.can_walk, False)
            for terrain in ("rock", "sand", "cliff"):
                with self.subTest(terrain=terrain):
                    with self.assertRaises(BasaltLegsDamaged):
                        basalt.move(1, terrain)
            self.assertEqual(snapshot(basalt), before)

    def test_tc18_move_check_priority(self):
        """TC-18. При нескольких нарушениях — первое по порядку SPEC 6.3."""
        with self.subTest(case="2 лапы + нет энергии"):
            basalt = make_basalt(energy=0)
            damage(basalt, 4)
            with self.assertRaises(BasaltLegsDamaged):
                basalt.move(1, "rock")

        with self.subTest(case="2 лапы + перегруз"):
            basalt = make_basalt(mass_kg=400)
            damage(basalt, 4)
            with self.assertRaises(BasaltLegsDamaged):
                basalt.move(1, "cliff")

        with self.subTest(case="перегруз + нет энергии"):
            basalt = make_basalt(mass_kg=400, energy=0)
            with self.assertRaises(BasaltGripFailure):
                basalt.move(1, "cliff")

        with self.subTest(case="только нет энергии"):
            basalt = make_basalt(energy=0)
            with self.assertRaises(BasaltNoStrength):
                basalt.move(1, "rock")

        with self.subTest(case="вода + 2 лапы"):
            basalt = make_basalt()
            damage(basalt, 4)
            with self.assertRaises(BasaltCannotSwim):
                basalt.move(1, "water")

        with self.subTest(case="вода + нет энергии"):
            basalt = make_basalt(energy=0)
            with self.assertRaises(BasaltCannotSwim):
                basalt.move(1, "water")

        with self.subTest(case="вода + нулевая дистанция"):
            basalt = make_basalt()
            with self.assertRaises(ValueError):
                basalt.move(0, "water")

        with self.subTest(case="неверный тип + неизвестная поверхность"):
            basalt = make_basalt()
            with self.assertRaises(TypeError):
                basalt.move("1", "space")


class TestCalculateEnergy(unittest.TestCase):
    """SPEC 3.4.3."""

    def test_tc19_calculate_energy_values(self):
        """TC-19. Расчёт расхода без изменения состояния и без проверок домена."""
        basalt = make_basalt()
        before = snapshot(basalt)

        self.assertAlmostEqual(basalt.calculate_energy(10, "rock"), 10.0,
                               places=PLACES)
        self.assertAlmostEqual(basalt.calculate_energy(10, "sand"), 20.0,
                               places=PLACES)
        self.assertAlmostEqual(basalt.calculate_energy(10, "cliff"), 40.0,
                               places=PLACES)
        self.assertEqual(snapshot(basalt), before)

        poor = make_basalt(energy=10)
        self.assertAlmostEqual(poor.calculate_energy(1000, "cliff"), 4000.0,
                               places=PLACES)
        self.assertAlmostEqual(poor.energy, 10.0, places=PLACES)

        crippled = make_basalt()
        damage(crippled, 4)
        self.assertAlmostEqual(crippled.calculate_energy(10, "rock"), 10.0,
                               places=PLACES)

        heavy = make_basalt(mass_kg=400)
        self.assertAlmostEqual(heavy.calculate_energy(10, "cliff"), 40.0,
                               places=PLACES)

    def test_tc20_calculate_energy_errors(self):
        """TC-20. Ошибки параметров и вода в calculate_energy."""
        basalt = make_basalt()

        with self.assertRaises(BasaltCannotSwim):
            basalt.calculate_energy(1, "water")
        for args in ((0, "rock"), (1, "air")):
            with self.subTest(args=args):
                with self.assertRaises(ValueError):
                    basalt.calculate_energy(*args)
        with self.assertRaises(TypeError):
            basalt.calculate_energy("1", "rock")


class TestCanOvercome(unittest.TestCase):
    """SPEC 3.4.2."""

    def _states(self):
        standing = make_basalt()

        on_cliff = make_basalt()
        on_cliff.move(1, "cliff")

        heavy = make_basalt(mass_kg=400)

        four_legs = make_basalt(mass_kg=300)
        damage(four_legs, 2)

        three_legs_light = make_basalt(mass_kg=100)
        damage(three_legs_light, 3)

        exhausted = make_basalt(energy=0)

        exhausted_on_cliff = make_basalt(energy=100)
        exhausted_on_cliff.move(25, "cliff")

        two_legs = make_basalt()
        damage(two_legs, 4)

        return {
            "стоит на земле": (
                standing, {"wall": True, "river": False, "boulder": True}),
            "на скале": (
                on_cliff, {"wall": True, "river": False, "boulder": True}),
            "перегруз 400 кг": (
                heavy, {"wall": False, "river": False, "boulder": True}),
            "4 лапы, 300 кг": (
                four_legs, {"wall": False, "river": False, "boulder": True}),
            "3 лапы, 100 кг": (
                three_legs_light,
                {"wall": True, "river": False, "boulder": False}),
            "энергия 0 на земле": (
                exhausted, {"wall": False, "river": False, "boulder": False}),
            "энергия 0 на скале": (
                exhausted_on_cliff,
                {"wall": True, "river": False, "boulder": False}),
            "2 лапы": (
                two_legs, {"wall": False, "river": False, "boulder": False}),
        }

    def test_tc21_can_overcome_matrix(self):
        """TC-21. Правила препятствий в разных состояниях; состояние не меняется."""
        for state_name, (basalt, expected) in self._states().items():
            for obstacle, result in expected.items():
                with self.subTest(state=state_name, obstacle=obstacle):
                    before = snapshot(basalt)

                    actual = basalt.can_overcome(obstacle)

                    self.assertIs(actual, result)
                    self.assertEqual(snapshot(basalt), before)

    def test_tc22_can_overcome_invalid(self):
        """TC-22. Неизвестное препятствие → ValueError, не строка → TypeError."""
        basalt = make_basalt()

        for obstacle in ("mountain", ""):
            with self.subTest(obstacle=obstacle):
                with self.assertRaises(ValueError):
                    basalt.can_overcome(obstacle)
        for obstacle in (42, None):
            with self.subTest(obstacle=obstacle):
                with self.assertRaises(TypeError):
                    basalt.can_overcome(obstacle)


class TestRefuel(unittest.TestCase):
    """SPEC 3.4.4."""

    def test_tc23_refuel(self):
        """TC-23. Подзарядка пополняет энергию, но не выше 100."""
        for start, amount, expected in ((20, 50, 70.0),
                                        (50, 1000, 100.0),
                                        (100, 0.5, 100.0)):
            with self.subTest(start=start, amount=amount):
                basalt = make_basalt(energy=start)

                result = basalt.refuel(amount)

                self.assertIsNone(result)
                self.assertAlmostEqual(basalt.energy, expected, places=PLACES)

    def test_tc24_refuel_invalid(self):
        """TC-24. Неположительная или нечисловая подзарядка отвергается."""
        basalt = make_basalt(energy=50)

        for amount in (0, -5):
            with self.subTest(amount=amount):
                with self.assertRaises(ValueError):
                    basalt.refuel(amount)
        for amount in ("10", True):
            with self.subTest(amount=amount):
                with self.assertRaises(TypeError):
                    basalt.refuel(amount)
        self.assertAlmostEqual(basalt.energy, 50.0, places=PLACES)


class TestLegs(unittest.TestCase):
    """SPEC 3.4.5, 3.4.6."""

    def test_tc25_damage_leg_on_cliff(self):
        """TC-25. Повреждение лапы: срыв со скалы при нарушении сцепления."""
        with self.subTest(case="на скале, mass 300"):
            basalt = make_basalt()
            basalt.move(2, "cliff")

            basalt.damage_leg()

            self.assertEqual(basalt.working_legs, 5)
            self.assertAlmostEqual(basalt.grip_capacity_kg, 300.0,
                                   places=PLACES)
            self.assertIs(basalt.is_climbing, True)
            self.assertIs(basalt.can_climb, True)

            basalt.damage_leg()

            self.assertEqual(basalt.working_legs, 4)
            self.assertAlmostEqual(basalt.grip_capacity_kg, 240.0,
                                   places=PLACES)
            self.assertIs(basalt.is_climbing, False)
            self.assertIs(basalt.can_climb, False)
            self.assertAlmostEqual(basalt.energy, 92.0, places=PLACES)
            self.assertAlmostEqual(basalt.position_km, 2.0, places=PLACES)

        with self.subTest(case="на земле"):
            basalt = make_basalt()

            basalt.damage_leg()

            self.assertEqual(basalt.working_legs, 5)
            self.assertAlmostEqual(basalt.energy, 100.0, places=PLACES)
            self.assertAlmostEqual(basalt.position_km, 0.0, places=PLACES)
            self.assertIs(basalt.is_climbing, False)

        with self.subTest(case="лёгкий аппарат срывается при менее чем 3 лапах"):
            basalt = make_basalt(mass_kg=100)
            basalt.move(1, "cliff")

            damage(basalt, 3)

            self.assertEqual(basalt.working_legs, 3)
            self.assertIs(basalt.is_climbing, True)

            basalt.damage_leg()

            self.assertEqual(basalt.working_legs, 2)
            self.assertIs(basalt.is_climbing, False)

    def test_tc26_damage_leg_lower_bound(self):
        """TC-26. Число исправных лап не опускается ниже 0."""
        basalt = make_basalt()

        damage(basalt, 7)

        self.assertEqual(basalt.working_legs, 0)
        self.assertAlmostEqual(basalt.grip_capacity_kg, 0.0, places=PLACES)
        self.assertIs(basalt.can_walk, False)
        self.assertIs(basalt.can_climb, False)

    def test_tc27_repair_legs(self):
        """TC-27. Ремонт восстанавливает все лапы; остальное не меняется."""
        with self.subTest(case="после повреждений на земле"):
            basalt = make_basalt()
            damage(basalt, 3)

            basalt.repair_legs()

            self.assertEqual(basalt.working_legs, 6)
            self.assertAlmostEqual(basalt.grip_capacity_kg, 360.0,
                                   places=PLACES)
            self.assertIs(basalt.can_climb, True)
            self.assertIs(basalt.is_climbing, False)

        with self.subTest(case="лапы и так исправны"):
            basalt = make_basalt()
            basalt.repair_legs()
            self.assertEqual(basalt.working_legs, 6)

        with self.subTest(case="на скале"):
            basalt = make_basalt()
            basalt.move(1, "cliff")
            before = snapshot(basalt)
            basalt.repair_legs()
            self.assertIs(basalt.is_climbing, True)
            self.assertEqual(snapshot(basalt), before)


class TestStatusAndExceptions(unittest.TestCase):
    """SPEC 3.4.7, 6.1."""

    def test_tc28_get_status(self):
        """TC-28. Статус: ровно нужные ключи, верные значения, это копия."""
        basalt = make_basalt()
        basalt.move(10, "rock")

        status = basalt.get_status()

        self.assertEqual(
            set(status),
            {"name", "energy", "position_km", "is_climbing",
             "working_legs", "can_walk", "can_climb"},
        )
        self.assertEqual(status["name"], "Базальт")
        self.assertAlmostEqual(status["energy"], 90.0, places=PLACES)
        self.assertAlmostEqual(status["position_km"], 10.0, places=PLACES)
        self.assertIs(status["is_climbing"], False)
        self.assertEqual(status["working_legs"], 6)
        self.assertIsInstance(status["working_legs"], int)
        self.assertIs(status["can_walk"], True)
        self.assertIs(status["can_climb"], True)

        status["energy"] = 0.0
        status["working_legs"] = 0
        self.assertAlmostEqual(basalt.energy, 90.0, places=PLACES)
        self.assertEqual(basalt.working_legs, 6)

    def test_tc29_exception_hierarchy(self):
        """TC-29. Иерархия доменных исключений."""
        for exc in (BasaltCannotSwim, BasaltNoStrength,
                    BasaltGripFailure, BasaltLegsDamaged):
            with self.subTest(exc=exc.__name__):
                self.assertTrue(issubclass(exc, BasaltError))
        self.assertTrue(issubclass(BasaltError, CrazyVehicleError))
        self.assertTrue(issubclass(CrazyVehicleError, Exception))

        error = BasaltNoStrength(required=6, available=2)
        self.assertAlmostEqual(error.required, 6.0, places=PLACES)
        self.assertAlmostEqual(error.available, 2.0, places=PLACES)

# Сценарные тесты


class TestScenarios(unittest.TestCase):
    """SPEC 4.2"""

    def test_tc30_mountain_shelter_delivery(self):
        """TC-30. Сценарий 5 «Доставка груза в горный приют»."""
        # Given эталонный «Базальт» с энергией 100 стоит на земле
        basalt = make_basalt()
        pilot = Pilot(basalt)

        # When пилот идёт по камням 12 км
        hours = pilot.идти_по_камням(12)
        # Then время 1.0 ч, энергия 88, пройдено 12 км, не на скале
        self.assertAlmostEqual(hours, 1.0, places=PLACES)
        self.assertAlmostEqual(basalt.energy, 88.0, places=PLACES)
        self.assertAlmostEqual(basalt.position_km, 12.0, places=PLACES)
        self.assertIs(basalt.is_climbing, False)

        # When пилот проверяет валун и стену / Then может и то и другое
        self.assertIs(pilot.может_преодолеть("boulder"), True)
        self.assertIs(pilot.может_преодолеть("wall"), True)

        # When пилот лезет на скалу 1.5 км
        hours = pilot.лезть_на_скалу(1.5)
        # Then время 0.5 ч, энергия 82, пройдено 13.5 км, на скале
        self.assertAlmostEqual(hours, 0.5, places=PLACES)
        self.assertAlmostEqual(basalt.energy, 82.0, places=PLACES)
        self.assertAlmostEqual(basalt.position_km, 13.5, places=PLACES)
        self.assertIs(basalt.is_climbing, True)

        # When пилот проверяет реку / Then не может
        self.assertIs(pilot.может_преодолеть("river"), False)

        # When пилот пытается переплыть 1 км / Then BasaltCannotSwim
        before = snapshot(basalt)
        with self.assertRaises(BasaltCannotSwim):
            pilot.переплыть(1)
        self.assertEqual(snapshot(basalt), before)

        # When пилот спускается 1.5 км
        hours = pilot.спуститься(1.5)
        # Then время 0.125 ч, энергия 80.5, пройдено 15 км, не на скале
        self.assertAlmostEqual(hours, 0.125, places=PLACES)
        self.assertAlmostEqual(basalt.energy, 80.5, places=PLACES)
        self.assertAlmostEqual(basalt.position_km, 15.0, places=PLACES)
        self.assertIs(basalt.is_climbing, False)

        # When пилот идёт по песку 3 км
        hours = pilot.идти_по_песку(3)
        # Then время 0.5 ч, энергия 74.5, пройдено 18 км
        self.assertAlmostEqual(hours, 0.5, places=PLACES)
        self.assertAlmostEqual(basalt.energy, 74.5, places=PLACES)
        self.assertAlmostEqual(basalt.position_km, 18.0, places=PLACES)

        # When пилот пытается лезть на скалу 20 км
        with self.assertRaises(BasaltNoStrength) as ctx:
            pilot.лезть_на_скалу(20)
        # Then нужно 80, есть 74.5, состояние прежнее
        self.assertAlmostEqual(ctx.exception.required, 80.0, places=PLACES)
        self.assertAlmostEqual(ctx.exception.available, 74.5, places=PLACES)
        self.assertAlmostEqual(basalt.position_km, 18.0, places=PLACES)
        self.assertAlmostEqual(basalt.energy, 74.5, places=PLACES)
        self.assertIs(basalt.is_climbing, False)

        # When пилот подзаряжается на 30 / Then энергия 100 (потолок)
        pilot.подзарядиться(30)
        self.assertAlmostEqual(basalt.energy, 100.0, places=PLACES)

        # When пилот лезет на скалу 10 км
        hours = pilot.лезть_на_скалу(10)
        # Then время 3.333333 ч, энергия 60, пройдено 28 км, на скале
        self.assertAlmostEqual(hours, 10 / 3, places=PLACES)
        self.assertAlmostEqual(basalt.energy, 60.0, places=PLACES)
        self.assertAlmostEqual(basalt.position_km, 28.0, places=PLACES)
        self.assertIs(basalt.is_climbing, True)

    def test_tc31_rockfall_on_ledge(self):
        """TC-31. Сценарий 6 «Обвал на карнизе»."""
        # Given эталонный «Базальт» с энергией 100
        basalt = make_basalt()
        pilot = Pilot(basalt)
        rockfall = Rockfall()
        workshop = Workshop()

        # When пилот лезет на скалу 2 км
        hours = pilot.лезть_на_скалу(2)
        # Then время 0.666667 ч, энергия 92, пройдено 2 км, на скале
        self.assertAlmostEqual(hours, 2 / 3, places=PLACES)
        self.assertAlmostEqual(basalt.energy, 92.0, places=PLACES)
        self.assertAlmostEqual(basalt.position_km, 2.0, places=PLACES)
        self.assertIs(basalt.is_climbing, True)

        # When обвал выводит из строя одну лапу
        rockfall.обрушить(basalt)
        # Then 5 лап, 300 кг; масса равна грузоподъёмности — держится
        self.assertEqual(basalt.working_legs, 5)
        self.assertAlmostEqual(basalt.grip_capacity_kg, 300.0, places=PLACES)
        self.assertIs(basalt.is_climbing, True)
        self.assertIs(basalt.can_climb, True)

        # When обвал выводит из строя ещё одну лапу
        rockfall.обрушить(basalt)
        # Then 4 лапы, 240 кг; аппарат сорвался
        self.assertEqual(basalt.working_legs, 4)
        self.assertAlmostEqual(basalt.grip_capacity_kg, 240.0, places=PLACES)
        self.assertIs(basalt.is_climbing, False)
        self.assertIs(basalt.can_climb, False)
        self.assertAlmostEqual(basalt.energy, 92.0, places=PLACES)
        self.assertAlmostEqual(basalt.position_km, 2.0, places=PLACES)

        # When пилот пытается лезть на скалу 1 км / Then BasaltGripFailure
        with self.assertRaises(BasaltGripFailure):
            pilot.лезть_на_скалу(1)
        self.assertAlmostEqual(basalt.energy, 92.0, places=PLACES)
        self.assertAlmostEqual(basalt.position_km, 2.0, places=PLACES)

        # When пилот проверяет стену и валун
        # Then стену не может, валун может (4 лапы)
        self.assertIs(pilot.может_преодолеть("wall"), False)
        self.assertIs(pilot.может_преодолеть("boulder"), True)

        # When пилот идёт по камням 3 км
        hours = pilot.идти_по_камням(3)
        # Then время 0.25 ч, энергия 89, пройдено 5 км
        self.assertAlmostEqual(hours, 0.25, places=PLACES)
        self.assertAlmostEqual(basalt.energy, 89.0, places=PLACES)
        self.assertAlmostEqual(basalt.position_km, 5.0, places=PLACES)

        # When обвал выводит из строя ещё две лапы
        rockfall.обрушить(basalt)
        rockfall.обрушить(basalt)
        # Then 2 лапы, ходить нельзя
        self.assertEqual(basalt.working_legs, 2)
        self.assertIs(basalt.can_walk, False)

        # When пилот пытается идти по камням 1 км / Then BasaltLegsDamaged
        with self.assertRaises(BasaltLegsDamaged):
            pilot.идти_по_камням(1)
        self.assertAlmostEqual(basalt.energy, 89.0, places=PLACES)
        self.assertAlmostEqual(basalt.position_km, 5.0, places=PLACES)

        # When пилот проверяет валун / Then не может
        self.assertIs(pilot.может_преодолеть("boulder"), False)

        # When мастерская чинит лапы
        workshop.починить_лапы(basalt)
        # Then 6 лап, можно лезть, по-прежнему не на скале
        self.assertEqual(basalt.working_legs, 6)
        self.assertIs(basalt.can_climb, True)
        self.assertIs(basalt.is_climbing, False)

        # When пилот лезет на скалу 2 км
        hours = pilot.лезть_на_скалу(2)
        # Then время 0.666667 ч, энергия 81, пройдено 7 км, на скале
        self.assertAlmostEqual(hours, 2 / 3, places=PLACES)
        self.assertAlmostEqual(basalt.energy, 81.0, places=PLACES)
        self.assertAlmostEqual(basalt.position_km, 7.0, places=PLACES)
        self.assertIs(basalt.is_climbing, True)

    def test_tc32_heavyweight_at_river(self):
        """TC-32. Сценарий 7 «Тяжеловес у реки»."""
        # Given «Тяжеловес»: 400 кг, 12 км/ч, энергия 100
        basalt = make_basalt(name="Тяжеловес", mass_kg=400)
        pilot = Pilot(basalt)
        # Then грузоподъёмность сцепления 360, лезть нельзя, ходить можно
        self.assertAlmostEqual(basalt.grip_capacity_kg, 360.0, places=PLACES)
        self.assertIs(basalt.can_climb, False)
        self.assertIs(basalt.can_walk, True)

        # When пилот пытается лезть на скалу 1 км / Then BasaltGripFailure
        with self.assertRaises(BasaltGripFailure):
            pilot.лезть_на_скалу(1)
        self.assertAlmostEqual(basalt.position_km, 0.0, places=PLACES)
        self.assertAlmostEqual(basalt.energy, 100.0, places=PLACES)

        # When пилот проверяет стену и реку / Then не может ни то ни другое
        self.assertIs(pilot.может_преодолеть("wall"), False)
        self.assertIs(pilot.может_преодолеть("river"), False)

        # When пилот пытается переплыть 1 км / Then BasaltCannotSwim
        before = snapshot(basalt)
        with self.assertRaises(BasaltCannotSwim):
            pilot.переплыть(1)
        self.assertEqual(snapshot(basalt), before)

        # When пилот идёт по камням 20 км вдоль реки
        hours = pilot.идти_по_камням(20)
        # Then время 1.666667 ч, энергия 80, пройдено 20 км
        self.assertAlmostEqual(hours, 20 / 12, places=PLACES)
        self.assertAlmostEqual(basalt.energy, 80.0, places=PLACES)
        self.assertAlmostEqual(basalt.position_km, 20.0, places=PLACES)

        # When пилот идёт по песку 40 км
        hours = pilot.идти_по_песку(40)
        # Then время 6.666667 ч, энергия 0, пройдено 60 км, ходить нельзя
        self.assertAlmostEqual(hours, 40 / 6, places=PLACES)
        self.assertAlmostEqual(basalt.energy, 0.0, places=PLACES)
        self.assertAlmostEqual(basalt.position_km, 60.0, places=PLACES)
        self.assertIs(basalt.can_walk, False)

        # When пилот пытается пройти по камням ещё 1 км
        with self.assertRaises(BasaltNoStrength) as ctx:
            pilot.идти_по_камням(1)
        # Then нужно 1, есть 0
        self.assertAlmostEqual(ctx.exception.required, 1.0, places=PLACES)
        self.assertAlmostEqual(ctx.exception.available, 0.0, places=PLACES)

        # When пилот подзаряжается на 1000 / Then энергия 100
        pilot.подзарядиться(1000)
        self.assertAlmostEqual(basalt.energy, 100.0, places=PLACES)

        # Then итог
        self.assertAlmostEqual(basalt.position_km, 60.0, places=PLACES)
        self.assertIs(basalt.is_climbing, False)
        self.assertIs(basalt.can_climb, False)

    def test_tc33_last_push_on_cliff(self):
        """TC-33. Сценарий 8 «Последний рывок на скале»."""
        # Given эталонный «Базальт» с энергией 100
        basalt = make_basalt()
        pilot = Pilot(basalt)

        # When пилот лезет на скалу 25 км
        hours = pilot.лезть_на_скалу(25)
        # Then время 8.333333 ч, энергия 0, пройдено 25 км, на скале
        self.assertAlmostEqual(hours, 25 / 3, places=PLACES)
        self.assertAlmostEqual(basalt.energy, 0.0, places=PLACES)
        self.assertAlmostEqual(basalt.position_km, 25.0, places=PLACES)
        self.assertIs(basalt.is_climbing, True)
        # And лезть дальше не может, но стену преодолеет, реку — нет
        self.assertIs(basalt.can_climb, False)
        self.assertIs(pilot.может_преодолеть("wall"), True)
        self.assertIs(pilot.может_преодолеть("river"), False)

        # When пилот пытается лезть ещё 0.25 км / Then нужно 1, есть 0
        with self.assertRaises(BasaltNoStrength) as ctx:
            pilot.лезть_на_скалу(0.25)
        self.assertAlmostEqual(ctx.exception.required, 1.0, places=PLACES)
        self.assertAlmostEqual(ctx.exception.available, 0.0, places=PLACES)
        self.assertAlmostEqual(basalt.position_km, 25.0, places=PLACES)

        # When пилот подзаряжается на 4 / Then энергия 4, может лезть
        pilot.подзарядиться(4)
        self.assertAlmostEqual(basalt.energy, 4.0, places=PLACES)
        self.assertIs(basalt.can_climb, True)

        # When пилот лезет на скалу 1 км
        hours = pilot.лезть_на_скалу(1)
        # Then время 0.333333 ч, энергия 0, пройдено 26 км, на скале
        self.assertAlmostEqual(hours, 1 / 3, places=PLACES)
        self.assertAlmostEqual(basalt.energy, 0.0, places=PLACES)
        self.assertAlmostEqual(basalt.position_km, 26.0, places=PLACES)
        self.assertIs(basalt.is_climbing, True)

    def test_tc34_exact_grip_capacity(self):
        """TC-34. Сценарий 9 «Впритык по сцеплению»."""
        # Given «Ровня»: 240 кг, 8 км/ч, энергия 40
        basalt = make_basalt(name="Ровня", mass_kg=240,
                             max_speed_kmh=8, energy=40)
        pilot = Pilot(basalt)
        rockfall = Rockfall()
        workshop = Workshop()

        # When обвал выводит из строя две лапы
        rockfall.обрушить(basalt)
        rockfall.обрушить(basalt)
        # Then 4 лапы, 240 кг; масса равна грузоподъёмности, можно лезть
        self.assertEqual(basalt.working_legs, 4)
        self.assertAlmostEqual(basalt.grip_capacity_kg, 240.0, places=PLACES)
        self.assertIs(basalt.can_climb, True)

        # When пилот лезет на скалу 5 км
        hours = pilot.лезть_на_скалу(5)
        # Then время 2.5 ч, энергия 20, пройдено 5 км, на скале
        self.assertAlmostEqual(hours, 2.5, places=PLACES)
        self.assertAlmostEqual(basalt.energy, 20.0, places=PLACES)
        self.assertAlmostEqual(basalt.position_km, 5.0, places=PLACES)
        self.assertIs(basalt.is_climbing, True)

        # When обвал выводит из строя ещё одну лапу
        rockfall.обрушить(basalt)
        # Then 3 лапы, 180 кг; аппарат сорвался
        self.assertEqual(basalt.working_legs, 3)
        self.assertAlmostEqual(basalt.grip_capacity_kg, 180.0, places=PLACES)
        self.assertIs(basalt.is_climbing, False)

        # When пилот пытается лезть на скалу 1 км / Then BasaltGripFailure
        with self.assertRaises(BasaltGripFailure):
            pilot.лезть_на_скалу(1)

        # When пилот идёт по камням 10 км
        hours = pilot.идти_по_камням(10)
        # Then время 1.25 ч, энергия 10, пройдено 15 км
        self.assertAlmostEqual(hours, 1.25, places=PLACES)
        self.assertAlmostEqual(basalt.energy, 10.0, places=PLACES)
        self.assertAlmostEqual(basalt.position_km, 15.0, places=PLACES)

        # When пилот идёт по песку 5 км
        hours = pilot.идти_по_песку(5)
        # Then время 1.25 ч, энергия 0, пройдено 20 км
        self.assertAlmostEqual(hours, 1.25, places=PLACES)
        self.assertAlmostEqual(basalt.energy, 0.0, places=PLACES)
        self.assertAlmostEqual(basalt.position_km, 20.0, places=PLACES)

        # When мастерская чинит лапы
        workshop.починить_лапы(basalt)
        # Then 6 лап, но can_climb == False, потому что энергия 0
        self.assertEqual(basalt.working_legs, 6)
        self.assertIs(basalt.can_climb, False)

        # When пилот пытается лезть на скалу 1 км / Then нужно 4, есть 0
        with self.assertRaises(BasaltNoStrength) as ctx:
            pilot.лезть_на_скалу(1)
        self.assertAlmostEqual(ctx.exception.required, 4.0, places=PLACES)
        self.assertAlmostEqual(ctx.exception.available, 0.0, places=PLACES)
        self.assertIs(basalt.is_climbing, False)


if __name__ == "__main__":
    unittest.main()