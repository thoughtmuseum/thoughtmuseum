from django import template

register = template.Library()


@register.filter('has_group')
def has_group(user, group_name):
    groups = user.groups.all().values_list('name', flat=True)
    return True if group_name in groups else False


@register.simple_tag
def exam_results(exam, user):
    return exam.get_results(user)
