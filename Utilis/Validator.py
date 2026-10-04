import string
import bcrypt

class Validator:

    @staticmethod
    def validate_password(password: str):
        letters = list(string.ascii_lowercase)
        special_symbols = list(string.punctuation)
        numbers = list(string.digits)
        count_of_special_signs = 0
        count_of_numbers = 0
        count_of_letters = 0

        if len(password) >= 8:
            for symbol in password.lower().strip():
                if symbol in letters:
                    count_of_letters += 1
                elif symbol in special_symbols:
                    count_of_special_signs += 1
                elif symbol in numbers:
                    count_of_numbers += 1

            return all(x > 0 for x in (count_of_numbers,count_of_letters,count_of_special_signs))

        else:
            return False

    @staticmethod
    def make_hash(password: str):
        hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        return hashed_password

    @staticmethod
    def check_password(password: str, hash: bytes):
        return bcrypt.checkpw(password.encode(), hash)

    @staticmethod
    def check_payment_amount(amount: str):
        if not amount.isdigit():
            return False
        amount = int(amount)

        return amount >= 0








