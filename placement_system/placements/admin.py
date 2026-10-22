
from django.contrib import admin
from .models import Student, Company, Application


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'register_number', 'department', 'cgpa')
    search_fields = ('name', 'register_number', 'department')


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('id', 'company_name', 'job_role', 'salary', 'eligibility')
    search_fields = ('company_name', 'job_role')


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('id', 'student', 'company', 'status', 'applied_at')
    list_filter = ('status', 'company')
    search_fields = ('student__username', 'company__company_name')
    list_editable = ('status',)
    readonly_fields = ('applied_at',)


