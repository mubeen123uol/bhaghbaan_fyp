from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Diagnosis, ChatSession, ChatMessageAI
from .services import AIDoctorService

def diagnose_view(request):
    """Leaf photo upload, camera capture, and instant AI Plant Doctor diagnosis."""
    if request.method == 'POST':
        image = request.FILES.get('image')
        if not image:
            messages.error(request, "براہ کرم پودے کی تصویر اپلوڈ کریں۔")
            return redirect('diagnose')

        if image.size > 5 * 1024 * 1024:
            messages.error(request, "تصویر کا سائز 5 ایم بی سے کم ہونا چاہیے۔")
            return redirect('diagnose')

        lang = request.POST.get('language', 'ur')
        city = request.user.city if request.user.is_authenticated else 'Lahore'

        try:
            diag = AIDoctorService.diagnose_image(
                user=request.user if request.user.is_authenticated else None,
                image_file=image,
                language=lang,
                city=city
            )
            return redirect('diagnosis-result', pk=diag.pk)
        except ValueError as ve:
            messages.error(request, str(ve))
            return redirect('diagnose')
        except Exception as e:
            messages.error(request, f"تشخیص میں دشواری: {str(e)}")
            return redirect('diagnose')

    return render(request, 'ai_doctor/diagnose.html')

def diagnosis_result(request, pk):
    """Rich diagnosis result with organic/chemical tabs, confidence meter, and escalation."""
    diag = get_object_or_404(Diagnosis, pk=pk)
    return render(request, 'ai_doctor/diagnosis_result.html', {'diagnosis': diag})

@login_required
def diagnosis_history(request):
    diagnoses = Diagnosis.objects.filter(user=request.user)
    return render(request, 'ai_doctor/diagnosis_history.html', {'diagnoses': diagnoses})

@login_required
def chatbot_view(request):
    """Bilingual voice/text interactive gardening chatbot."""
    session = ChatSession.objects.filter(user=request.user).first()
    if not session:
        session = ChatSession.objects.create(user=request.user)
    history = session.messages.all()

    if request.method == 'POST':
        user_message = request.POST.get('message', '').strip()
        if user_message:
            lang = request.POST.get('language') or request.session.get('django_language') or getattr(request.user, 'preferred_language', 'en') or 'en'
            reply = AIDoctorService.ask_chatbot(request.user, session.id, user_message, request_lang=lang)
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.POST.get('ajax') == '1':
                return JsonResponse({'reply': reply, 'user_message': user_message})
            return redirect('chatbot')

    return render(request, 'ai_doctor/chatbot.html', {
        'session': session,
        'history': history,
    })

@login_required
def chatbot_clear_view(request):
    """Clear conversation history for the current user's session."""
    session = ChatSession.objects.filter(user=request.user).first()
    if session:
        session.messages.all().delete()
        lang = request.session.get('django_language') or getattr(request.user, 'preferred_language', 'en') or 'en'
        msg = "Chat history cleared successfully." if lang == 'en' else "چیٹ ہسٹری صاف کر دی گئی ہے۔"
        messages.success(request, msg)
    return redirect('chatbot')
