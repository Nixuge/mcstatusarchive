class Status:
    # current_values: dict
    # normal_values_tuple: tuple
    # null_values_tuple: tuple
    null_args_order: tuple[str]
    
    def _get_changed_properties(self, previous_values: dict) -> list[str]:
        changed_values = []
        for key, value in self.current_values.items():
            if previous_values.get(key) != value or previous_values.get(key) == None:
                changed_values.append(key)
            
        return changed_values
    
    def get_data_tuple(self, previous_values: dict) -> tuple[bool, tuple]:
        new_tuple: list[str] = []
        for val in self.normal_values_tuple:
            new_tuple.append(val)
        
        # print(previous_values)
# 
        changed_values = self._get_changed_properties(previous_values)

        for val in self.null_args_order:
            if val in changed_values:
                new_tuple.append(self.current_values.get(val))
            else:
                new_tuple.append(None)
        

        return len(changed_values) > 0, new_tuple
