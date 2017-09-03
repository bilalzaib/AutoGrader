from django import template
from django.template.defaultfilters import stringfilter
import os
from AutoGrade.models import SUBMISSION_STATUS

register = template.Library()

@register.filter(name='basename')
@stringfilter
def basename(value):
    return os.path.basename(value)

@register.filter(name='submission_queue_status')
def submission_queue_status(value):
    if value and SUBMISSION_STATUS[int(value)][1]:
        return SUBMISSION_STATUS[int(value)][1]
    else:
        return "N/A"