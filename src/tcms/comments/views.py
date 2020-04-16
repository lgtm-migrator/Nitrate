# -*- coding: utf-8 -*-

import logging

from django.conf import settings
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import JsonResponse
from django.shortcuts import render
from django.views import generic
from django.views.decorators.http import require_POST

import django_comments.signals
from django_comments.views.moderation import perform_delete

from tcms.comments.models import post_comment
from tcms.comments.exceptions import InvalidCommentPostRequest

log = logging.getLogger(__name__)


@require_POST
def post(request, template_name='comments/comments.html'):
    """Post a comment"""
    data = request.POST.copy()
    try:
        target, _ = post_comment(
            data, request.user, request.META.get('REMOTE_ADDR'))
    except InvalidCommentPostRequest as e:
        target = e.target
    return render(request, template_name, context={'object': target})


class DeleteCommentView(PermissionRequiredMixin, generic.View):
    """Delete comment from given objects"""

    permission_required = 'django_comments.can_moderate'

    def post(self, request):
        comments = django_comments.get_model().objects.filter(
            pk__in=request.POST.getlist('comment_id'),
            site__pk=settings.SITE_ID,
            is_removed=False,
            user_id=request.user.id
        )

        if not comments:
            return JsonResponse({'rc': 1, 'response': 'Object does not exist.'})

        # Flag the comment as deleted instead of actually deleting it.
        for comment in comments:
            perform_delete(request, comment)

        return JsonResponse({'rc': 0, 'response': 'ok'})
