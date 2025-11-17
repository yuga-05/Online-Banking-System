# This file makes the utils directory a Python package
# Import common utility functions for easier access

from .helpers import (
    generate_account_number,
    generate_transaction_id,
    calculate_age,
    format_currency,
    allowed_file,
    save_profile_image,
    calculate_loan_interest,
    calculate_loan_payment,
    format_date,
    get_transaction_description
)

from .validators import (
    validate_email,
    validate_password,
    validate_name,
    validate_phone,
    validate_dob,
    validate_amount,
    validate_passcode,
    validate_account_number,
    validate_uid,
    validate_address,
    validate_loan_amount
)

from .decorators import (
    login_required,
    admin_required,
    account_owner_required,
    prevent_authenticated
)