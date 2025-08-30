from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, HttpResponse
from django.views.generic import ListView
from django.core.paginator import Paginator
from django.db.models import Q, Count
import pandas as pd
from .models import Worker, Company, Contractor, Work, Department
from .forms import UploadEmployeeDataForm, LogoUploadForm, BulkActionForm
import gspread
from google.oauth2.service_account import Credentials
import os
from django.conf import settings
from .forms import RegistrationForm
from .models import User

def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create profile based on user_type
            if user.user_type == 'company':
                Company.objects.create(user=user)
            elif user.user_type == 'contractor':
                # Note: Contractor requires a company; for simplicity, assign to first company or handle later
                company = Company.objects.first()  # Placeholder; improve as needed
                Contractor.objects.create(user=user, company=company)
            elif user.user_type == 'worker':
                # Similar placeholder
                company = Company.objects.first()
                Worker.objects.create(user=user, company=company, name=user.username)
            return redirect('login')
    else:
        form = RegistrationForm()
    return render(request, 'core/register.html', {'form': form})

@login_required
def dashboard_redirect(request):
    if request.user.user_type == 'company':
        return redirect('company_dashboard')
    elif request.user.user_type == 'contractor':
        return redirect('contractor_dashboard')
    elif request.user.user_type == 'worker':
        return redirect('worker_dashboard')
    return HttpResponseForbidden()

class WorkerListView(ListView):
    model = Worker
    template_name = 'core/company_dashboard.html'
    paginate_by = 20

    def get_queryset(self):
        if self.request.user.user_type != 'company':
            return Worker.objects.none()
        qs = Worker.objects.filter(company=self.request.user.company_profile)
        search = self.request.GET.get('search')
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(role__icontains=search) | Q(skill__icontains=search))
        department = self.request.GET.get('department')
        if department:
            qs = qs.filter(department__id=department)
        skill = self.request.GET.get('skill')
        if skill:
            qs = qs.filter(skill__icontains=skill)
        location = self.request.GET.get('location')
        if location:
            qs = qs.filter(location__icontains=location)
        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)
        order_by = self.request.GET.get('order_by', 'name')
        if order_by == 'joining_date':
            qs = qs.order_by('joining_date')
        elif order_by == 'role':
            qs = qs.order_by('role')
        else:
            qs = qs.order_by('name')
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = UploadEmployeeDataForm()
        context['bulk_form'] = BulkActionForm(company=self.request.user.company_profile)
        context['departments'] = Department.objects.all()
        context['logo_form'] = LogoUploadForm(instance=self.request.user.company_profile)
        # Analytics
        qs = self.get_queryset()
        context['total_workers'] = qs.count()
        context['dept_dist'] = qs.values('department__name').annotate(count=Count('department__name'))
        context['active_count'] = qs.filter(status='active').count()
        context['inactive_count'] = qs.filter(status='inactive').count()
        return context

    def post(self, request, *args, **kwargs):
        if 'bulk_action' in request.POST:
            bulk_form = BulkActionForm(request.POST, company=request.user.company_profile)
            if bulk_form.is_valid():
                action = bulk_form.cleaned_data['action']
                ids = request.POST.getlist('workers')
                workers = Worker.objects.filter(id__in=ids, company=request.user.company_profile)
                if action == 'delete':
                    workers.delete()
                elif action == 'assign':
                    contractor = bulk_form.cleaned_data['contractor']
                    workers.update(contractor=contractor)
            return redirect('company_dashboard')
        elif 'logo' in request.FILES:
            logo_form = LogoUploadForm(request.POST, request.FILES, instance=request.user.company_profile)
            if logo_form.is_valid():
                logo_form.save()
            return redirect('company_dashboard')
        else:
            form = UploadEmployeeDataForm(request.POST, request.FILES)
            errors = []
            if form.is_valid():
                file = form.cleaned_data.get('file')
                google_url = form.cleaned_data.get('google_sheet_url')
                data = []
                if file:
                    if file.name.endswith('.csv'):
                        df = pd.read_csv(file)
                    else:
                        df = pd.read_excel(file)
                    data = df.to_dict('records')
                elif google_url:
                    try:
                        scopes = ['https://www.googleapis.com/auth/spreadsheets.readonly']
                        creds_file = os.path.join(settings.BASE_DIR, 'service_account.json')
                        credentials = Credentials.from_service_account_file(creds_file, scopes=scopes)
                        gc = gspread.authorize(credentials)
                        sheet = gc.open_by_url(google_url)
                        worksheet = sheet.get_worksheet(0)
                        data = worksheet.get_all_records()
                    except Exception as e:
                        errors.append(str(e))
                for row in data:
                    try:
                        dept_name = row.get('department')
                        dept = Department.objects.filter(name=dept_name).first() if dept_name else None
                        Worker.objects.create(
                            company=request.user.company_profile,
                            name=row.get('name', ''),
                            role=row.get('role', ''),
                            department=dept,
                            skill=row.get('skill', ''),
                            location=row.get('location', ''),
                            status=row.get('status', 'active'),
                            joining_date=row.get('joining_date'),
                            tags=row.get('tags', ''),
                            notes=row.get('notes', ''),
                            contact=row.get('contact', '')
                        )
                    except Exception as e:
                        errors.append(f"Row {row}: {e}")
            if errors:
                request.session['upload_errors'] = errors  # Display in template if needed
            return redirect('company_dashboard')
        return self.get(request, *args, **kwargs)

@login_required
def export_workers(request):
    if request.user.user_type != 'company':
        return HttpResponseForbidden()
    qs = Worker.objects.filter(company=request.user.company_profile).values()
    df = pd.DataFrame(list(qs))
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="workers.csv"'
    df.to_csv(path_or_buf=response, index=False)
    return response

@login_required
def company_monitor_contractors(request):
    if request.user.user_type != 'company':
        return HttpResponseForbidden()
    contractors = Contractor.objects.filter(company=request.user.company_profile)
    works = Work.objects.filter(company=request.user.company_profile)
    return render(request, 'core/company_monitor.html', {'contractors': contractors, 'works': works})

@login_required
def contractor_dashboard(request):
    if request.user.user_type != 'contractor':
        return HttpResponseForbidden()
    contractor = request.user.contractor_profile
    works = Work.objects.filter(contractor=contractor)
    # Chart data
    status_counts = works.values('status').annotate(count=Count('status'))
    labels = [item['status'] for item in status_counts]
    data = [item['count'] for item in status_counts]
    logo_form = LogoUploadForm(instance=contractor)
    if request.method == 'POST':
        logo_form = LogoUploadForm(request.POST, request.FILES, instance=contractor)
        if logo_form.is_valid():
            logo_form.save()
    return render(request, 'core/contractor_dashboard.html', {
        'works': works,
        'departments': Department.objects.all(),
        'chart_labels': labels,
        'chart_data': data,
        'logo_form': logo_form
    })

@login_required
def worker_dashboard(request):
    if request.user.user_type != 'worker':
        return HttpResponseForbidden()
    worker = request.user.worker_profile
    return render(request, 'core/worker_dashboard.html', {
        'worker': worker,
        'departments': Department.objects.all()
    })

@login_required
def department_tracking(request):
    departments = Department.objects.all()
    # Filter by department if GET param
    dept_id = request.GET.get('department')
    works = Work.objects.all()
    workers = Worker.objects.all()
    if dept_id:
        works = works.filter(department_id=dept_id)
        workers = workers.filter(department_id=dept_id)
    return render(request, 'core/department_tracking.html', {'departments': departments, 'works': works, 'workers': workers})