from secrets import choice
from django.conf import settings as django_settings
from rest_framework_simplejwt.tokens import RefreshToken
from auth_app.models import User
from random import shuffle
from typing import Optional, Union

import jwt as py_jwt
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey
from jwt import ExpiredSignatureError, InvalidTokenError
from jwt.algorithms import RSAAlgorithm
from auth_app.constants import FormatRegex


from auth_app import logger


class JWTUtils:
    """
    Utilities for basic operation on JWT.
    """
    HS256_ALGORITHM_NAME: str = 'HS256'
    RS256_ALGORITHM_NAME: str = 'RS256'

    @classmethod
    def get_tokens_for_user(cls, user: User = None):
        if not user:
            logger.warning(f'Invalid argument(s) NULL `user` passed.')
            return None
        if not isinstance(user, User):
            logger.warning(f'Invalid argument(s) `user` passed.')
            return None

        if not user in User.objects.all():
            logger.warning(f'Invalid argument(s) `user` does not exist.')
            return None
        refresh = RefreshToken.for_user(user)

        return {
            'refreshToken': str(refresh),
            'accessToken': str(refresh.access_token),
        }

    @classmethod
    def decode_jwt_token(
        cls,
        token: str = None,
        algorithm: str = 'HS256',
        public_signing_key: Optional[Union[str, dict]] = None,
        issuer: str = None,
        audience: str = None,
    ):
        """
        Decode and validate a JWT token.

        `token`:
            The JWT token string to be decoded and validated.

        `algorithm`:
            The algorithm used to encode the JWT; can be `HS256` | `RS256`.

        `public_signing_key`: 
            The key used to sign the JWT. The value of `public_signing_key` can be either a string or a dictionary.

            - For Elay's internal JWTs the value of `public_signing_key` is the value of the web-apllication's `SECRET_KEY` setting.

            - For 3rd party JWTs, the value of `public_signing_key` can be:
                - A string containing the public key in PEM format (PKCS/X.509/SPKI).
                - A dictionary containing the public key in JWK format.
        """
        if not token:
            logger.warning(f'Invalid argument(s) NULL `token` passed.')
            return None

        if django_settings.DEBUG:
            logger.info(
                f"Token:\t{token}\nAlgorithm:\t{algorithm}\nSigning Key:\t{public_signing_key}")

        try:
            if algorithm == cls.HS256_ALGORITHM_NAME:
                if not public_signing_key:
                    # prithoo: In case of `HS256`, the `signing_key` is the secret key.
                    public_signing_key = django_settings.SECRET_KEY
                valid_data = py_jwt.decode(jwt=token, key=public_signing_key, algorithms=[
                                           cls.HS256_ALGORITHM_NAME])

            elif algorithm == cls.RS256_ALGORITHM_NAME:
                rsa_key: Union[RSAPublicKey, bytes] = None
                decode_options = {
                    "verify_aud": False,
                    "verify_iss": bool(issuer),
                    "verify_exp": True,
                    "verify_nbf": True,
                    "verify_iat": True,
                    "require": [
                        "exp",
                        "iat",
                        "sub"
                    ]
                }
                leeway_seconds = 120

                if not public_signing_key:
                    logger.warning(
                        f'Invalid argument(s) NULL `signing_key` passed for `RS256` algorithm.')
                    return None

                if isinstance(public_signing_key, dict):
                    # prithoo: This means the pubKey is in JWK format.
                    rsa_key = RSAAlgorithm.from_jwk(jwk=public_signing_key)
                elif isinstance(public_signing_key, str):
                    # prithoo: This means the pubKey is in PKCS | X.509 | SPKI formats.
                    rsa_key = public_signing_key.encode('utf-8')
                else:
                    logger.warning(
                        f'Invalid argument(s) `signing_key` passed for `RS256` algorithm. The value must be either a string or a dictionary.')
                    return None

                if not rsa_key:
                    logger.warning(f'Error while converting JWK to RSA key.')
                    return None

                valid_data = py_jwt.decode(
                    jwt=token,
                    key=rsa_key,
                    algorithms=[cls.RS256_ALGORITHM_NAME],
                    issuer=issuer,
                    audience=audience,
                    options=decode_options,
                    leeway=leeway_seconds
                )

            else:
                logger.warning(f'Unsupported algorithm `{algorithm}` passed.')
                return None

            return valid_data

        except ExpiredSignatureError as sig_ex:
            logger.warning(f'The token has expired. Error: {sig_ex}')
            return None
        except InvalidTokenError as inv_ex:
            logger.warning(f'The token is invalid. Error: {inv_ex}')
            return None
        except Exception as ex:
            logger.warning(f'Error while decoding JWT token. Error: {ex}')
            return None


class PasswordUtils:
    LOWERCASE_LETTERS = ('a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k',
                         'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z')
    UPPERCASE_LETTERS = ('A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K',
                         'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z')
    DIGITS = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9)
    SPECIAL_CHARACTERS = ('@', '#', '$', '%', '&', '*',
                          '-', '_', '=', '+', '!', '?')

    MAX_ITERATION: int = 7

    @classmethod
    def generate_strong_password(
        cls,
        uc_letters_count: int = 2,
        lc_letters_count: int = 12,
        digits_count: int = 2,
        special_characters_count: int = 4,
        min_length: int = 18,
        max_length: int = 64,
        iteration: int = 0
    ):
        """
        Generate a strong password that meets our password policy requirements.

        Our current password policy requires:
            - At least 1 uppercase letter
            - At least 1 lowercase letter
            - At least 1 digit
            - At least 1 special character
            - Minimum length of 8 characters
            - Maximum length of 64 characters

        These requirements are enforced via `FormatRegex.PASSWORD_REGEX` and are used as the
        default values for the parameters of this method.

        With default parameters, generates a password of exactly 20 characters (2+12+2+4).
        The min_length and max_length parameters are used for validation when custom 
        character counts are provided to ensure the total character count falls within 
        the specified range.

        Uses recursive approach to maintain complete randomness - if the generated password
        fails regex validation, the entire password is regenerated from scratch rather than
        making incremental fixes. Limited to MAX_ITERATION attempts to prevent infinite recursion.

        Args:
            uc_letters_count: Number of uppercase letters (default: 2)
            lc_letters_count: Number of lowercase letters (default: 12) 
            digits_count: Number of digits (default: 2)
            special_characters_count: Number of special characters (default: 4)
            min_length: Minimum allowed total length for validation (default: 18)
            max_length: Maximum allowed total length for validation (default: 64)
            iteration: Internal recursion counter (default: 0)

        Returns:
            str: A randomly generated password meeting the specified requirements

        Raises:
            ValueError: If character counts don't fit within min_length/max_length range
        """
        letters = []

        if min_length <= 0 or max_length <= 0:
            raise ValueError(
                "min_length and max_length must be non-negative integers.")

        if max_length < min_length:
            max_length = 2*min_length

        total_characters_count = uc_letters_count + \
            lc_letters_count + digits_count + special_characters_count
        if total_characters_count > max_length or total_characters_count < min_length:
            raise ValueError(
                f"Total characters count {total_characters_count} is not in the range of min_length {min_length} and max_length {max_length}.")

        for _ in range(uc_letters_count):
            letters.append(choice(cls.UPPERCASE_LETTERS))

        for _ in range(lc_letters_count):
            letters.append(choice(cls.LOWERCASE_LETTERS))

        for _ in range(digits_count):
            letters.append(str(choice(cls.DIGITS)))

        for _ in range(special_characters_count):
            letters.append(choice(cls.SPECIAL_CHARACTERS))

        shuffle(letters)
        password = ''.join(letters)
        if not FormatRegex.PASSWORD_REGEX.match(password) and iteration < cls.MAX_ITERATION:
            return cls.generate_strong_password(
                uc_letters_count=uc_letters_count,
                lc_letters_count=lc_letters_count,
                digits_count=digits_count,
                special_characters_count=special_characters_count,
                min_length=min_length,
                max_length=max_length,
                iteration=iteration + 1
            )
        return password
