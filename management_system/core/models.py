from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError

class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('company', 'Company'),
        ('contractor', 'Contractor'),
        ('worker', 'Worker'),
    )
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES)

class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Company(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='company_profile')
    logo = models.ImageField(upload_to='logos/', blank=True)

    def __str__(self):
        return self.user.username

class Contractor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='contractor_profile')
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    logo = models.ImageField(upload_to='logos/', blank=True)

    def __str__(self):
        return self.user.username

class Worker(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('on_leave', 'On Leave'),
    )
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='worker_profile')
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    contractor = models.ForeignKey(Contractor, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=100, blank=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    skill = models.CharField(max_length=200, blank=True)
    location = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='active')
    joining_date = models.DateField(null=True, blank=True)
    tags = models.CharField(max_length=200, blank=True)  # e.g., "Certified Electrician,On Leave"
    notes = models.TextField(blank=True)
    contact = models.CharField(max_length=200, blank=True)  # e.g., email/phone

    def __str__(self):
        return self.name

    def clean(self):
        if not self.name:
            raise ValidationError('Name is required.')
        # Other validations can be added

    def has_missing_fields(self):
        return not all([self.name, self.role, self.department, self.status])

class Work(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)
    contractor = models.ForeignKey(Contractor, on_delete=models.CASCADE)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='pending')
    updates = models.TextField(blank=True)

    def __str__(self):
        return self.name