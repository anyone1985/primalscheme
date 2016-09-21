from django.contrib import messages
from django.template.loader import render_to_string


def messages_to_json(request):
    json = {'messages': []}
    for message in messages.get_messages(request):
        json['messages'].append({
            "level": message.level,
            "level_tag": message.level_tag,
            "message": message.message,
        })
    json['messages_html'] = render_to_string(
        'home/includes/messages.html',
        {'messages': messages.get_messages(request)})
    return json
