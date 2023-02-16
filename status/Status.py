class Status:
    current_values: tuple[str]
    
    def _get_changed_properties(self, previous_values: tuple[str]) -> list[str]:
        changed_values = []
        for key, value in enumerate(self.current_values):
            if previous_values[key] != value or previous_values[key] == None:
                changed_values.append(key)
            
        return changed_values
    
    def get_data_tuple(self, previous_values: dict) -> tuple[bool, tuple]:
        new_tuple: list[str] = []

        changed_values = self._get_changed_properties(previous_values)

        for index, val in enumerate(self.current_values):
            if index in changed_values:
                new_tuple.append(self.current_values[index])
            else:
                new_tuple.append(None)
        
        # returning a list instead of a tuple, big lie
        return len(changed_values) > 0, new_tuple
