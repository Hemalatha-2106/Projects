from django.db import models
from django.contrib.auth.models import User
class Student(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='student_profile'
    )

    name = models.CharField(max_length=100)
    register_number = models.CharField(
        max_length=20,
        unique=True
    )
    department = models.CharField(max_length=50)
    cgpa = models.FloatField()

    def __str__(self):
        return self.name
class Company(models.Model):
    company_name = models.CharField(max_length=100)
    job_role = models.CharField(max_length=100)
    salary = models.CharField(max_length=50)
    eligibility = models.CharField(max_length=100)

    def __str__(self):
        return self.company_name
class Application(models.Model):
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='job_applications'
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='applications'
    )
    status = models.CharField(max_length=20, default='Applied')
    applied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'company')

    def __str__(self):
        return f"{self.student.username} - {self.company.company_name}"