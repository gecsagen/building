from django.contrib import admin
from .models import Building, Section, Expenditure


@admin.register(Building)
class BuildingAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ("building", "parent")
    search_fields = ("building__name", "parent__name")
    list_filter = ("building",)


@admin.register(Expenditure)
class ExpenditureAdmin(admin.ModelAdmin):
    list_display = ("section", "name", "type", "count", "price")
    search_fields = ("name", "section__building__name", "section__parent__name")
    list_filter = ("type", "section__building")
