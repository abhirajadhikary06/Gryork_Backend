from django.contrib import admin
from .models import User, Department, Company, Contractor, Worker, Work

admin.site.register(User)
admin.site.register(Department)
admin.site.register(Company)
admin.site.register(Contractor)
admin.site.register(Worker)
admin.site.register(Work)