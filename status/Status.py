from abc import abstractmethod

class Status:
    current_values: dict
    normal_values_tuple: tuple
    null_values_tuple: tuple
    null_null_tuple: tuple

    def _has_property_changed(self, previous_values: dict):
        for key, value in self.current_values.items():
            if previous_values.get(key) != value:
                return True
        # for key, old_value in previous_values.items():
        #     if self.current_values.get(key) != old_value:
        #         return True
        return False
    
    def get_data_tuple(self, previous_values: dict) -> tuple[bool, tuple]:
        if self._has_property_changed(previous_values):
            return True, self.normal_values_tuple + self.null_values_tuple
        else:
            return False, self.normal_values_tuple + self.null_null_tuple