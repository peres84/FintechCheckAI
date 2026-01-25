import re

#Other files imports
from src.utils.custom_logger import log_handler
from src.configuration.config_loader import config
from fastapi import HTTPException

def validate_email_format(email: str) -> bool:
    """
        Validate an email address.
        
        local_part@subdomain.domain.tld or example@provider.tld

        Checks if:
        - There is exactly one '@' symbol.
        - The local part is non-empty, contains no '@' and only allowed characters.
        - The domain contains exactly 1 '.' separating provider and TLD.
        - The provider and TLD are in allowed lists from config.

        Args:
            email (str): The email string to validate.

        Returns:
            Nothing, it allows execution and not raise an exception
    """
    
    message = ""
    
    #Check exactly one '@' in the email
    if email.count('@') != 1:
        message=f"Invalid email '{email}': must contain exactly one '@'"
        log_handler.warning(message)
        raise HTTPException(status_code=400, detail=message)
    local_part, domain_part = email.rsplit('@', 1)

    #Check local part is not empty and contains only allowed characters
    if not local_part or not re.match(r'^[\w\.-]+$', local_part):
        message=f"Invalid email '{email}': local part is invalid"
        log_handler.warning(message)
        raise HTTPException(status_code=400, detail=message)
    
    #Domain must contain exactly one '.'
    if domain_part.count('.') != 1:
        message=f"Invalid email '{email}': domain part must contain exactly one '.'"
        log_handler.warning(message)
        raise HTTPException(status_code=400, detail=message)
    provider, tld = domain_part.rsplit('.', 1)

    #Check if provider and tld are allowed
    if provider not in config["email_validation"]["allowed_providers"]:
        message=f"Invalid email '{email}': provider '{provider}' not allowed"
        log_handler.warning(message)
        raise HTTPException(status_code=400, detail=message)
    if tld not in config["email_validation"]["allowed_tlds"]:
        message=f"Invalid email '{email}': TLD '{tld}' not allowed"
        log_handler.warning(message)
        raise HTTPException(status_code=400, detail=message)

    log_handler.debug(f"Email '{email}' is valid, proceeding")

def validate_password_format(password: str):
    """
        Validate a password.

        Checks if:
        - At least 8 characters long
        - Contains at least one lowercase letter
        - Contains at least one uppercase letter
        - Contains at least one digit
        - Contains at least one special symbol (non-alphanumeric)

        Args:
            password (str): The password string to validate.

        Returns:
            bool: Nothing, the method does not raise exceptions and allows
            to continue execution
    """

    message = ""

    if len(password) < 8:
        message= "Password length is too short."
        log_handler.warning(message) 
        raise HTTPException(status_code=400, detail=message)

    if not re.search(r"[a-z]", password):
        message= "Password validation failed: no lowercase letter found"
        log_handler.warning(message) 
        raise HTTPException(status_code=400, detail=message)

    if not re.search(r"[A-Z]", password):
        message= "Password validation failed: no uppercase letter found"
        log_handler.warning(message)
        raise HTTPException(status_code=400, detail=message)

    if not re.search(r"\d", password):
        message= "Password validation failed: no digit found"
        log_handler.warning(message)
        raise HTTPException(status_code=400, detail=message)

    if not re.search(r"[^\w\s]", password):
        message= "Password validation failed: no special symbol found"
        log_handler.warning(message)
        raise HTTPException(status_code=400, detail=message)

    log_handler.info("Password is valid") 
