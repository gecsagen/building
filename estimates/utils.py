import typing as t
from decimal import Decimal

from django.db import models, transaction
from django.db.models import DecimalField, F, Sum

from .models import Building, Expenditure, Section


def get_parent_sections(building_id: int) -> t.List[dict]:
    """
    Возвращает список родительских секций для указанного здания с рассчитанным бюджетом для каждой секции.

    @param building_id: Идентификатор здания
    @return: Список словарей с информацией о секции и ее бюджете
    """
    # Получаем все родительские секции
    parent_sections = Section.objects.filter(
        building_id=building_id, parent__isnull=True
    )

    result = []
    for section in parent_sections:
        # Рассчитываем общий бюджет для всех дочерних секций данной родительской секции
        budget = (
            Expenditure.objects.filter(section__in=section.section_set.all()).aggregate(
                total=models.Sum(models.F("count") * models.F("price"))
            )["total"]
            or 0
        )

        result.append({"section": section, "budget": budget})

    return result


def get_buildings() -> t.List[dict]:
    """
    Возвращает список всех зданий с общей суммой расходов на работы и материалы для каждого здания.

    @return: Список словарей с информацией о здании и суммами расходов на работы и материалы
    """
    buildings = Building.objects.all()

    result = []
    for building in buildings:
        # Рассчитываем общую сумму расходов на работы для данного здания
        works_amount = (
            Expenditure.objects.filter(
                section__building=building, type=Expenditure.Types.WORK
            ).aggregate(
                total=Sum(F("count") * F("price"), output_field=DecimalField())
            )[
                "total"
            ]
            or 0
        )
        # Рассчитываем общую сумму расходов на материалы для данного здания
        materials_amount = (
            Expenditure.objects.filter(
                section__building=building, type=Expenditure.Types.MATERIAL
            ).aggregate(
                total=Sum(F("count") * F("price"), output_field=DecimalField())
            )[
                "total"
            ]
            or 0
        )

        result.append(
            {
                "id": building.id,
                "works_amount": works_amount,
                "materials_amount": materials_amount,
            }
        )

    return result


def update_with_discount(section_id: int, discount: Decimal):
    """
    Обновляет поле price у всех расценок внутри секции с учётом указанной скидки.

    @param section_id: ID секции, для которой применяется скидка
    @param discount: Размер скидки в процентах от Decimal(0) до Decimal(100)
    """
    if not (0 <= discount <= 100):
        raise ValueError("Скидка должна быть в пределах от 0 до 100")

    with transaction.atomic():
        # Выбираем текущую секцию и ее дочерние секции
        sections_to_update = Section.objects.filter(
            id=section_id
        ) | Section.objects.filter(parent_id=section_id)

        # Выбираем все расходы, относящиеся к выбранным секциям
        expenditures = Expenditure.objects.filter(section__in=sections_to_update)

        # Вычисляем коэффициент скидки
        discount = Decimal(discount)
        discount_factor = Decimal("1.00") - (discount / Decimal("100.00"))

        for expenditure in expenditures:
            expenditure.price *= discount_factor
            expenditure.save()
