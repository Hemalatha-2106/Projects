
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.contrib.admin.views.decorators import staff_member_required
from .models import Student, Company, Application


def home(request):
    return render(request, 'placements/home.html')

@staff_member_required
def add_student(request):
  def add_student(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        register_number = request.POST.get(
            'register_number', ''
        ).strip()
        department = request.POST.get('department', '').strip()
        cgpa_value = request.POST.get('cgpa', '').strip()

        if not all([name, register_number, department, cgpa_value]):
            return render(request, 'placements/add_student.html', {
                'error': 'All fields are required!'
            })

        try:
            cgpa = float(cgpa_value)
            if not 0 <= cgpa <= 10:
                raise ValueError

            Student.objects.create(
                name=name,
                register_number=register_number,
                department=department,
                cgpa=cgpa
            )

        except ValueError:
            return render(request, 'placements/add_student.html', {
                'error': 'Please enter a valid CGPA between 0 and 10!'
            })
        except Exception:
            return render(request, 'placements/add_student.html', {
                'error': 'Unable to add student. Check register number.'
            })

        return redirect('view_students')

    return render(request, 'placements/add_student.html')


def view_students(request):
    students = Student.objects.all().order_by('name')
    return render(request, 'placements/students.html', {
        'students': students
    })


def view_companies(request):
    query = request.GET.get('q', '').strip()
    companies = Company.objects.all().order_by('company_name')

    if query:
        companies = companies.filter(
            Q(company_name__icontains=query) |
            Q(job_role__icontains=query) |
            Q(eligibility__icontains=query)
        )

    return render(request, 'placements/companies.html', {
        'companies': companies,
        'query': query
    })


def register(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        name = request.POST.get('name', '').strip()
        register_number = request.POST.get(
            'register_number', ''
        ).strip()
        department = request.POST.get('department', '').strip()
        cgpa_value = request.POST.get('cgpa', '').strip()

        if not all([
            username, password, name,
            register_number, department, cgpa_value
        ]):
            return render(request, 'placements/register.html', {
                'error': 'Please fill in all fields!'
            })

        if User.objects.filter(username=username).exists():
            return render(request, 'placements/register.html', {
                'error': 'Username already exists!'
            })

        if Student.objects.filter(
            register_number__iexact=register_number
        ).exists():
            return render(request, 'placements/register.html', {
                'error': 'Register number already exists!'
            })

        if len(password) < 8:
            return render(request, 'placements/register.html', {
                'error': 'Password must contain at least 8 characters!'
            })

        try:
            cgpa = float(cgpa_value)
            if not 0 <= cgpa <= 10:
                raise ValueError
        except ValueError:
            return render(request, 'placements/register.html', {
                'error': 'Enter a valid CGPA between 0 and 10!'
            })

        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    username=username,
                    password=password
                )

                Student.objects.create(
                    user=user,
                    name=name,
                    register_number=register_number,
                    department=department,
                    cgpa=cgpa
                )

        except Exception as e:
            print("REGISTRATION ERROR:", repr(e))
            return render(request, 'placements/register.html', {
                'error': 'Registration failed. Please check the terminal error.'
            })

        return redirect('student_login')

    return render(request, 'placements/register.html')


def student_login(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:
            login(request, user)
            return redirect('student_home')

        return render(request, 'placements/login.html', {
            'error': 'Invalid username or password!'
        })

    return render(request, 'placements/login.html')


@login_required(login_url='student_login')
def student_home(request):
    return render(request, 'placements/student_home.html')


@login_required(login_url='student_login')
def student_dashboard(request):
    applications = Application.objects.filter(
        student=request.user
    ).select_related('company').order_by('-applied_at')

    context = {
        'total_applications': applications.count(),
        'selected_count': applications.filter(
            status='Selected'
        ).count(),
        'rejected_count': applications.filter(
            status='Rejected'
        ).count(),
        'pending_count': applications.filter(
            status='Applied'
        ).count(),
        'total_companies': Company.objects.count(),
        'recent_applications': applications[:5],
    }

    return render(
        request,
        'placements/student_dashboard.html',
        context
    )


@login_required(login_url='student_login')
def student_profile(request):
    student = Student.objects.filter(
        user=request.user
    ).first()

    return render(
        request,
        'placements/student_profile.html',
        {'student': student}
    )


@login_required(login_url='student_login')
def apply_job(request, company_id):
    company = get_object_or_404(Company, id=company_id)

    if request.method == 'POST':
        application, created = Application.objects.get_or_create(
            student=request.user,
            company=company
        )

        if created:
            message = 'Your application has been submitted successfully!'
        else:
            message = 'You have already applied for this company.'

        return render(request, 'placements/apply_job.html', {
            'company': company,
            'message': message,
            'submitted': True
        })

    return render(request, 'placements/apply_job.html', {
        'company': company,
        'submitted': False
    })


@login_required(login_url='student_login')
def my_applications(request):
    applications = Application.objects.filter(
        student=request.user
    ).select_related('company').order_by('-applied_at')

    return render(request, 'placements/my_applications.html', {
        'applications': applications
    })


@login_required(login_url='student_login')
def student_logout(request):
    if request.method == 'POST':
        logout(request)
        return redirect('student_login')

    return redirect('student_home')
