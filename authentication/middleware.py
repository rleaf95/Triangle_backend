from django.utils import translation

class UserLanguageMiddleware:
  def __init__(self, get_response):
    self.get_response = get_response

  def __call__(self, request):
    language = None
    
    if request.user.is_authenticated and request.user.language:
      language = request.user.language
    
    elif 'HTTP_ACCEPT_LANGUAGE' in request.META:
      accept_language = request.META['HTTP_ACCEPT_LANGUAGE']
      language = accept_language.split(',')[0].split('-')[0]
    
    if language:
      translation.activate(language)
      request.LANGUAGE_CODE = language
    
    response = self.get_response(request)
    
    translation.deactivate()
    
    return response