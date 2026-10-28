"""Модель шестилапого скалолаза «Базальт».

Публичный интерфейс и правила поведения реализованы по SPEC.md v0.2.
"""

from __future__ import annotations

import math
from typing import Final


class CrazyVehicleError(Exception):
    """Базовое исключение для ошибок транспортных моделей."""


class BasaltError(CrazyVehicleError):
    """Базовый класс доменных исключений «Базальта»."""


class BasaltCannotSwim(BasaltError):
    """Возникает при попытке перемещаться по воде."""

    def __init__(self, message: str = "basalt cannot swim: water short-circuits the drives") -> None:
        super().__init__(message)


class BasaltNoStrength(BasaltError):
    """Возникает, если энергии недостаточно для выбранного перемещения."""

    def __init__(self, required: float, available: float) -> None:
        self.required = float(required)
        self.available = float(available)
        super().__init__(
            f"not enough energy: required {self.required:g}, have {self.available:g}"
        )


class BasaltGripFailure(BasaltError):
    """Возникает, если масса аппарата превышает грузоподъёмность сцепления."""

    def __init__(self, mass_kg: float, grip_capacity_kg: float) -> None:
        self.mass_kg = float(mass_kg)
        self.grip_capacity_kg = float(grip_capacity_kg)
        super().__init__(
            "grip failure: mass "
            f"{self.mass_kg:g} kg, grip capacity {self.grip_capacity_kg:g} kg"
        )


class BasaltLegsDamaged(BasaltError):
    """Возникает, если исправных лап недостаточно для перемещения."""

    def __init__(self, working_legs: int) -> None:
        self.working_legs = int(working_legs)
        super().__init__(f"not enough working legs: {self.working_legs} of 6")


class BasaltClimber:
    """Шестилапый аппарат для движения по земле и подъёма по скалам.

    Все публичные атрибуты доступны только для чтения. Состояние изменяется
    методами перемещения, подзарядки, повреждения и ремонта лап.
    """

    LEG_COUNT: Final[int] = 6
    LEG_GRIP_CAPACITY_KG: Final[float] = 60.0
    MAX_ENERGY: Final[float] = 100.0

    _TERRAIN_ENERGY_RATE: Final[dict[str, float]] = {
        "rock": 1.0,
        "sand": 2.0,
        "cliff": 4.0,
    }
    _VALID_TERRAINS: Final[frozenset[str]] = frozenset(
        {"rock", "sand", "cliff", "water"}
    )
    _VALID_OBSTACLES: Final[frozenset[str]] = frozenset(
        {"wall", "river", "boulder"}
    )

    __slots__ = (
        "_name",
        "_mass_kg",
        "_max_speed_kmh",
        "_energy",
        "_position_km",
        "_is_climbing",
        "_leg_count",
        "_working_legs",
    )

    def __init__(
        self,
        name: str,
        mass_kg: float,
        max_speed_kmh: float,
        energy: float = 100.0,
    ) -> None:
        """Создать аппарат и проверить типы и диапазоны всех аргументов."""
        # Сначала проверяем типы всех аргументов, не проверяя их значения.
        if not isinstance(name, str):
            raise TypeError("name must be a string")
        self._require_number_type("mass_kg", mass_kg)
        self._require_number_type("max_speed_kmh", max_speed_kmh)
        self._require_number_type("energy", energy)

        # Все числовые значения проверяются на конечность до диапазонов.
        self._require_finite("mass_kg", mass_kg)
        self._require_finite("max_speed_kmh", max_speed_kmh)
        self._require_finite("energy", energy)

        if not name.strip():
            raise ValueError("name must not be empty")
        if mass_kg <= 0:
            raise ValueError("mass_kg must be positive")
        if max_speed_kmh <= 0:
            raise ValueError("max_speed_kmh must be positive")
        if not 0 <= energy <= self.MAX_ENERGY:
            raise ValueError("energy must be between 0 and 100")

        self._name = name
        self._mass_kg = float(mass_kg)
        self._max_speed_kmh = float(max_speed_kmh)
        self._energy = float(energy)
        self._position_km = 0.0
        self._is_climbing = False
        self._leg_count = self.LEG_COUNT
        self._working_legs = self.LEG_COUNT

    @staticmethod
    def _is_number(value: object) -> bool:
        """Вернуть True для int/float, исключая bool."""
        return isinstance(value, (int, float)) and not isinstance(value, bool)

    @classmethod
    def _require_number_type(cls, name: str, value: object) -> None:
        """Выбросить TypeError, если аргумент не является числом по контракту."""
        if not cls._is_number(value):
            raise TypeError(f"{name} must be a number")

    @staticmethod
    def _require_finite(name: str, value: int | float) -> None:
        """Запретить NaN и бесконечности на этапе проверки значений."""
        if not math.isfinite(float(value)):
            raise ValueError(f"{name} must be finite")

    @classmethod
    def _validate_move_arguments(
        cls, distance_km: object, terrain: object
    ) -> tuple[float, str]:
        """Проверить типы всех аргументов, затем значения и поверхность."""
        # Типы всех аргументов имеют приоритет над ошибками значений.
        cls._require_number_type("distance_km", distance_km)
        if not isinstance(terrain, str):
            raise TypeError("terrain must be a string")

        cls._require_finite("distance_km", distance_km)
        if distance_km <= 0:  # type: ignore[operator]
            raise ValueError("distance_km must be positive")
        if terrain not in cls._VALID_TERRAINS:
            raise ValueError(f"unknown terrain: {terrain}")
        return float(distance_km), terrain

    @staticmethod
    def _unknown_obstacle(obstacle: str) -> ValueError:
        """Сформировать единообразную ошибку для неизвестного препятствия."""
        return ValueError(f"unknown obstacle: {obstacle}")

    @property
    def name(self) -> str:
        """Имя аппарата."""
        return self._name

    @property
    def mass_kg(self) -> float:
        """Полная масса аппарата с пилотом, в килограммах."""
        return self._mass_kg

    @property
    def max_speed_kmh(self) -> float:
        """Максимальная скорость на твёрдой поверхности, км/ч."""
        return self._max_speed_kmh

    @property
    def energy(self) -> float:
        """Текущий запас энергии, условные единицы."""
        return self._energy

    @property
    def position_km(self) -> float:
        """Суммарное пройденное расстояние, км."""
        return self._position_km

    @property
    def is_climbing(self) -> bool:
        """Находится ли аппарат на отвесной скале."""
        return self._is_climbing

    @property
    def leg_count(self) -> int:
        """Общее число лап (всегда шесть)."""
        return self._leg_count

    @property
    def working_legs(self) -> int:
        """Текущее число исправных лап."""
        return self._working_legs

    @property
    def grip_capacity_kg(self) -> float:
        """Грузоподъёмность сцепления, кг."""
        return float(self._working_legs * self.LEG_GRIP_CAPACITY_KG)

    @property
    def can_walk(self) -> bool:
        """Может ли аппарат двигаться с учётом лап и наличия энергии."""
        return self._working_legs >= 3 and self._energy > 0

    @property
    def can_climb(self) -> bool:
        """Может ли аппарат начать подъём на скалу в текущем состоянии."""
        return (
            self._working_legs >= 3
            and self._mass_kg <= self.grip_capacity_kg
            and self._energy > 0
        )

    def move(self, distance_km: float, terrain: str) -> float:
        """Переместить аппарат и вернуть длительность перемещения в часах.

        Все проверки выполняются до изменения состояния. При любой ошибке
        энергия, положение и флаг подъёма остаются без изменений.
        """
        distance, surface = self._validate_move_arguments(distance_km, terrain)

        # Вода запрещена независимо от состояния остальных подсистем.
        if surface == "water":
            raise BasaltCannotSwim()

        # Очерёдность доменных проверок задана SPEC 3.4.1 и 6.3.
        if self._working_legs < 3:
            raise BasaltLegsDamaged(self._working_legs)
        if surface == "cliff" and self._mass_kg > self.grip_capacity_kg:
            raise BasaltGripFailure(self._mass_kg, self.grip_capacity_kg)

        energy_rate = self._TERRAIN_ENERGY_RATE[surface]
        required_energy = distance * energy_rate
        if required_energy > self._energy:
            raise BasaltNoStrength(required_energy, self._energy)

        speed_multiplier = {"rock": 1.0, "sand": 0.5, "cliff": 0.25}[surface]
        effective_speed = self._max_speed_kmh * speed_multiplier
        duration_hours = distance / effective_speed

        # Commit состояния выполняется только после успешного завершения проверок.
        self._energy = max(0.0, self._energy - required_energy)
        self._position_km += distance
        self._is_climbing = surface == "cliff"
        return float(duration_hours)

    def can_overcome(self, obstacle: str) -> bool:
        """Проверить преодолимость препятствия без изменения состояния."""
        if not isinstance(obstacle, str):
            raise TypeError("obstacle must be a string")
        if obstacle not in self._VALID_OBSTACLES:
            raise self._unknown_obstacle(obstacle)

        if obstacle == "wall":
            # Нахождение на скале делает это свойство True даже при energy == 0.
            return self._is_climbing or self.can_climb
        if obstacle == "river":
            return False
        return self._working_legs >= 4 and self._energy > 0

    def calculate_energy(self, distance_km: float, terrain: str) -> float:
        """Рассчитать расход энергии без проверки возможности перемещения."""
        distance, surface = self._validate_move_arguments(distance_km, terrain)
        if surface == "water":
            raise BasaltCannotSwim()
        return float(distance * self._TERRAIN_ENERGY_RATE[surface])

    def refuel(self, amount: float) -> None:
        """Пополнить энергию; запас не может превысить 100 единиц."""
        self._require_number_type("amount", amount)
        self._require_finite("amount", amount)
        if amount <= 0:
            raise ValueError("amount must be positive")
        self._energy = min(self.MAX_ENERGY, self._energy + float(amount))

    def damage_leg(self) -> None:
        """Вывести из строя одну лапу и сорвать аппарат при потере сцепления."""
        self._working_legs = max(0, self._working_legs - 1)
        if self._is_climbing and (
            self._working_legs < 3 or self._mass_kg > self.grip_capacity_kg
        ):
            self._is_climbing = False

    def repair_legs(self) -> None:
        """Восстановить все шесть лап без изменения остальных полей."""
        self._working_legs = self.LEG_COUNT

    def get_status(self) -> dict[str, str | float | bool | int]:
        """Вернуть независимую копию наблюдаемого состояния аппарата."""
        return {
            "name": self._name,
            "energy": self._energy,
            "position_km": self._position_km,
            "is_climbing": self._is_climbing,
            "working_legs": self._working_legs,
            "can_walk": self.can_walk,
            "can_climb": self.can_climb,
        }
