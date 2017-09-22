from enum import Enum

class PasswordTypes(Enum):
    PIN_FIXED_4 = 1
    MIXED_FIXED_8 = 2
    
    @classmethod
    def has_value(self, value):
        return (any(value == item.value for item in self))
