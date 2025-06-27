from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.http import JsonResponse
from smtplib import SMTPException
from django.contrib.auth.models import User
from django.urls import reverse


def ChangeInitiativeOwnerMail(request, oInitiative, selected_user_id):
    oNewOwner = User.objects.get(id=selected_user_id)
    subject = "Initiative Ownership change for "+ oInitiative.initiative_id + ' - ' + oInitiative.initiative_name
    
    text_content=""
    
    html_content = "<div class='container'>"
    html_content += "<div class='card'>"
    html_content += "<div class='card-header'>"
    html_content += "<p>Dear " + oNewOwner.first_name + " " + oNewOwner.last_name + ", </p>"
    html_content += "<hr>"
    html_content += "<p>" + request.user.get_full_name() + ", has reassigned this Initiative to you as the new Initiative Owner </p>"
    html_content += "</div>"
    html_content += "<div class='card-body text-center'>"
    html_content += "<p>Initiative name </p>"
    url = request.build_absolute_uri(reverse('Fit4:initiative_details', args=[oInitiative.slug]))
    html_content += f'<p><a href="{url}">' + oInitiative.initiative_name + '</a></p><br><br><br>'
    html_content += "<p>Previous Owner</p>"
    html_content += "<p>" + oInitiative.author.first_name + ", " + oInitiative.author.last_name + "</p>"
    html_content += "</div>"
    html_content += "</div>"
    html_content += "</div>"
    
    try:
        from_email = request.user.email
        to_email = [oNewOwner.email] # to whom the mail is going
        msg = EmailMultiAlternatives(subject, text_content, from_email, to_email)
        msg.attach_alternative(html_content, "text/html")
        msg.send()
    except SMTPException as e:
        return JsonResponse({'status':'error'})
    return JsonResponse({'status':'ok'})

def InitiativeOwnerSendmailToWorkStreamLead(request, oInitiative):
    #oInitiative = Initiative.objects.get(id=id)
    subject = "Approval request for "+ oInitiative.initiative_id + ' - ' + oInitiative.initiative_name
    
    text_content=""
    
    html_content = "<div class='container'>"
    html_content += "<div class='card'>"
    html_content += "<div class='card-header'>"
    html_content += "<p>Dear " + oInitiative.workstreamlead.first_name + " " + oInitiative.workstreamlead.last_name + ", </p>"
    html_content += "<hr>"
    html_content += "<p>" + request.user.get_full_name() + " has requested your approval for the following item: </p>"
    html_content += "</div>"
    html_content += "<div class='card-body text-center'>"
    html_content += "<p>Initiative name </p>"
    url = request.build_absolute_uri(reverse('Fit4:initiative_details', args=[oInitiative.slug]))
    html_content += f'<p><a href="{url}">' + oInitiative.initiative_name + '</a></p><br><br><br>'
    html_content += "<p>Owner</p>"
    html_content += "<p>" + oInitiative.author.first_name + ", " + oInitiative.author.last_name + "</p>"
    html_content += "<p>Comments</p>"
    html_content += "<p>" + oInitiative.next_Lgate_Comment + "</p>"
    html_content += "</div>"
    html_content += "</div>"
    html_content += "</div>"
    
    try:
        from_email = request.user.email
        to_email = [oInitiative.workstreamlead.email] # to whom the mail is going
        msg = EmailMultiAlternatives(subject, text_content, from_email, to_email)
        msg.attach_alternative(html_content, "text/html")
        msg.send()
    except SMTPException as e:
        return JsonResponse({'status':'error'})
    return JsonResponse({'status':'ok'})

def InitiativeOwnerSendmailToFinanceSponsor(request, oInitiative):
    #oInitiative = Initiative.objects.get(id=id)
    subject = "Approval request for "+ oInitiative.initiative_id + ' - ' + oInitiative.initiative_name
    
    text_content=""
    
    html_content = "<div class='container'>"
    html_content += "<div class='card'>"
    html_content += "<div class='card-header'>"
    html_content += "<p>Dear " + oInitiative.workstreamlead.first_name + " " + oInitiative.workstreamlead.last_name + ", </p>"
    html_content += "<hr>"
    html_content += "<p>" + request.user.get_full_name() + " has requested your approval for the following item: </p>"
    html_content += "</div>"
    html_content += "<div class='card-body text-center'>"
    html_content += "<p>Initiative name </p>"
    url = request.build_absolute_uri(reverse('Fit4:initiative_details', args=[oInitiative.slug]))
    html_content += f'<p><a href="{url}">' + oInitiative.initiative_name + '</a></p><br><br><br>'
    html_content += "<p>Owner</p>"
    html_content += "<p>" + oInitiative.author.first_name + ", " + oInitiative.author.last_name + "</p>"
    html_content += "<p>Comments</p>"
    html_content += "<p>" + oInitiative.next_Lgate_Comment + "</p>"
    html_content += "</div>"
    html_content += "</div>"
    html_content += "</div>"

    #context = {'request':request, 'user':user, 'event':event}
    #html_template = get_template("notifications/new_event_email.html").render(context)
    
    try:
        from_email = request.user.email
        to_email = [oInitiative.workstreamlead.email, request.user.email] # to whom the mail is going
        msg = EmailMultiAlternatives(subject, text_content, from_email, to_email) # bcc=to_email to be used in case you want to hise other receipients
        msg.attach_alternative(html_content, "text/html")
        msg.send()
    except SMTPException as e:
        return JsonResponse({'status':'error'})
    return JsonResponse({'status':'ok'})
    
def WorkStreamLeadSendmailToFinanceSponsorCopyInitiativeOwner(request, oInitiative):
    username = request.META['USERNAME']
    request.user = User.objects.get(username=username)
    
    subject = "Approval request for "+ oInitiative.initiative_id + ' - ' + oInitiative.initiative_name
    
    text_content=""
    
    html_content = "<div class='container'>"
    html_content += "<div class='card'>"
    html_content += "<div class='card-header'>"
    html_content += "<p>Dear " + oInitiative.financesponsor.first_name + " " + oInitiative.financesponsor.last_name + ", </p>"
    html_content += "<hr>"
    html_content += "<p>" + request.user.get_full_name() + " has requested your approval for the following item: </p>"
    html_content += "</div>"
    html_content += "<div class='card-body text-center'>"
    html_content += "<p>Initiative name </p>"
    url = request.build_absolute_uri(reverse('Fit4:initiative_details', args=[oInitiative.slug]))
    html_content += f'<p><a href="{url}">' + oInitiative.initiative_name + '</a></p><br><br><br>'
    html_content += "<p>Owner</p>"
    html_content += "<p>" + oInitiative.author.first_name + ", " + oInitiative.author.last_name + "</p>"
    html_content += "<p>Comments</p>"
    html_content += "<p>" + oInitiative.next_Lgate_Comment + "</p>"
    html_content += "</div>"
    html_content += "</div>"
    html_content += "</div>"
    
    try:
        from_email = request.user.email
        to_email = [oInitiative.financesponsor.email, oInitiative.author.email] # to whom the mail is going
        msg = EmailMultiAlternatives(subject, text_content, from_email, to_email)
        msg.attach_alternative(html_content, "text/html")
        msg.send()
    except SMTPException as e:
        return JsonResponse({'status':'error'})
    return JsonResponse({'status':'ok'})
    
def FinanceSponsorSendmailToInitiativeOwnerCopyWorkStreamLead(request, oInitiative):
    username = request.META['USERNAME']
    request.user = User.objects.get(username=username)
    
    subject = "Approval request for "+ oInitiative.initiative_id + ' - ' + oInitiative.initiative_name
    
    text_content=""
    
    html_content = "<div class='container'>"
    
    try:
        from_email = request.user.email
        to_email = [oInitiative.financesponsor.email, oInitiative.author.email] # to whom the mail is going
        msg = EmailMultiAlternatives(subject, text_content, from_email, to_email)
        msg.attach_alternative(html_content, "text/html")
        msg.send()
    except SMTPException as e:
        return JsonResponse({'status':'error'})
    return JsonResponse({'status':'ok'})
    
def FinanceSponsorSendmailToInitiativeOwnerCopyWorkStreamLead(request, oInitiative):
    username = request.META['USERNAME']
    request.user = User.objects.get(username=username)
    
    subject = "Approval request for "+ oInitiative.initiative_id + ' - ' + oInitiative.initiative_name
    
    text_content=""
    
    html_content = "<div class='container'>"
    
    try:
        from_email = request.user.email
        to_email = [oInitiative.financesponsor.email, oInitiative.author.email] # to whom the mail is going
        msg = EmailMultiAlternatives(subject, text_content, from_email, to_email)
        msg.attach_alternative(html_content, "text/html")
        msg.send()
    except SMTPException as e:
        return JsonResponse({'status':'error'})
    return JsonResponse({'status':'ok'})
    
def FinanceSponsorSendmailToWorkStreamSponsorCopyInitiativeOwner_WorkStreamLead(request, oInitiative):
    username = request.META['USERNAME']
    request.user = User.objects.get(username=username)
    
    subject = "Approval request for "+ oInitiative.initiative_id + ' - ' + oInitiative.initiative_name
    
    text_content=""
    
    html_content = "<div class='container'>"
    
    try:
        from_email = request.user.email
        to_email = [oInitiative.financesponsor.email, oInitiative.author.email] # to whom the mail is going
        msg = EmailMultiAlternatives(subject, text_content, from_email, to_email)
        msg.attach_alternative(html_content, "text/html")
        msg.send()
    except SMTPException as e:
        return JsonResponse({'status':'error'})
    return JsonResponse({'status':'ok'})
    
def FinanceSponsorSendmailToInitiativeOwner(request, oInitiative):
    username = request.META['USERNAME']
    request.user = User.objects.get(username=username)
    
    subject = "Approval request for "+ oInitiative.initiative_id + ' - ' + oInitiative.initiative_name
    
    text_content=""
    
    html_content = "<div class='container'>"
    
    try:
        from_email = request.user.email
        to_email = [oInitiative.financesponsor.email, oInitiative.author.email] # to whom the mail is going
        msg = EmailMultiAlternatives(subject, text_content, from_email, to_email)
        msg.attach_alternative(html_content, "text/html")
        msg.send()
    except SMTPException as e:
        return JsonResponse({'status':'error'})
    return JsonResponse({'status':'ok'})