from django.shortcuts import redirect, render


def error_test(request):
    if request.user.is_staff:
        raise Exception("This is a test of the emergency broadcast system.")
    else:
        return redirect('home')


def page_not_found_test(request):
    return render(request, '404.html')
