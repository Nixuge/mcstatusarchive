from abc import abstractmethod

class Status:
    current_values: dict
    normal_values_tuple: tuple
    null_values_tuple: tuple

    def _has_property_changed(self, previous_values: dict):
        for key, old_value in previous_values.items():
            if self.current_values.get(key) != old_value:
                print("WENT TRUE!!!")
                input()
                return True
        return False
    
    @abstractmethod
    def get_data_tuple(self, previous_values: dict):
        pass