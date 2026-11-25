from django.contrib import admin
from .models import Garden, GardenMember, Task, TaskReport, Expense

class GardenMemberInline(admin.TabularInline):
    model = GardenMember
    extra = 1

class ExpenseInline(admin.TabularInline):
    model = Expense
    extra = 0

@admin.register(Garden)
class GardenAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'city', 'total_budget', 'total_expenses', 'remaining_budget', 'created_at')
    search_fields = ('name', 'owner__username', 'location_address')
    inlines = [GardenMemberInline, ExpenseInline]

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'garden', 'state', 'assigned_to', 'due_date', 'updated_at')
    list_filter = ('state', 'garden')
    search_fields = ('title', 'description', 'assigned_to__username')

@admin.register(TaskReport)
class TaskReportAdmin(admin.ModelAdmin):
    list_display = ('task', 'submitted_at', 'reviewed_at')

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('title', 'garden', 'category', 'amount', 'recorded_by', 'expense_date')
    list_filter = ('category',)
    search_fields = ('title', 'garden__name')
