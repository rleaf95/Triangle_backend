import requests
from pathlib import Path
from django.core.cache import cache
from django.conf import settings
import logging

logger = logging.getLogger('django')


class DisposableEmailChecker:
  
  _disposable_domains = None
  
  @classmethod
  def _load_disposable_domains(cls):
    if cls._disposable_domains is not None:
      return cls._disposable_domains
    
    file_path = Path(__file__).parent / 'disposable_domains.txt'
    
    if not file_path.exists():
      logger.warning(f"Disposable domains file not found: {file_path}")
      cls._disposable_domains = {
        'tempmail.com', '10minutemail.com', 'guerrillamail.com',
        'mailinator.com', 'throwaway.email', 'temp-mail.org',
        'fakeinbox.com', 'trashmail.com', 'getnada.com',
        'maildrop.cc', 'yopmail.com', 'sharklasers.com',
        'getairmail.com', 'tempinbox.com', 'mintemail.com',
        'emailondeck.com', 'spamgourmet.com', 'mohmal.com',
        'mailnesia.com', 'guerrillamailblock.com', 'spam4.me',
      }
      return cls._disposable_domains
    
    try:
      with open(file_path, 'r', encoding='utf-8') as f:
        domains = {
          line.strip().lower() 
          for line in f 
          if line.strip() and not line.startswith('#')
        }
      
      logger.warning(f"Loaded {len(domains)} disposable email domains")
      cls._disposable_domains = domains
      return cls._disposable_domains
        
    except Exception as e:
      logger.error(f"Error loading disposable domains: {str(e)}")
      cls._disposable_domains = set()
      return cls._disposable_domains

  @classmethod
  def is_disposable(cls, email):
    if not email or '@' not in email:
      return False
    
    domain = email.split('@')[-1].lower()
    
    disposable_domains = cls._load_disposable_domains()

    if domain in disposable_domains:
      logger.info(f"Disposable email detected (local): {domain}")
      return True
    
    cache_key = f"disposable:{domain}"
    cached_result = cache.get(cache_key)
    if cached_result is not None:
      return cached_result
    
    use_api = getattr(settings, 'USE_DISPOSABLE_EMAIL_API', True)
    if use_api:
      is_disposable = cls._check_with_api(domain)
      cache.set(cache_key, is_disposable, 2592000)
      return is_disposable
  
    cache.set(cache_key, False, 2592000)
    return False
  
  
  @classmethod
  def _check_with_api(cls, domain):
    try:
      response = requests.get(
        f'https://open.kickbox.com/v1/disposable/{domain}',
        timeout=2
      )
      
      if response.status_code == 200:
        data = response.json()
        is_disposable = data.get('disposable', False)
        logger.warning(f"Loaded disposable email domains from kicbox")
        
        if is_disposable:
          logger.info(f"Disposable email detected (API): {domain}")
        
        return is_disposable
      else:
        logger.warning(f"Kickbox API returned status {response.status_code}")
        return False
        
    except requests.Timeout:
      logger.warning(f"Kickbox API timeout for domain: {domain}")
      return False
    except Exception as e:
      logger.error(f"Kickbox API error: {str(e)}")
      return False