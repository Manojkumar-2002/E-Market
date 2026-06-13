class SerializerErrorHandler:
    """Utility class for handling serializer errors"""

    @staticmethod
    def format_errors(serializer_errors):
        """Return errors without flattening, but only keep the first error per field"""

        def process(value):
            # Case 1: Nested dictionary -> recurse and keep the same structure
            if isinstance(value, dict):
                return {key: process(val) for key, val in value.items()}

            # Case 2: List -> needs special handling
            if isinstance(value, list):
                # 2A: List of error strings -> return first error
                if value and isinstance(value[0], str):
                    return value[0]

                # 2B: List of dicts -> process each dict
                if value and isinstance(value[0], dict):
                    return [process(item) for item in value]

                # 2C: List of lists -> take the first list & process it
                if value and isinstance(value[0], list):
                    return process(value[0])  # recursive on first list

                # 2D: Empty list -> generic message
                return "Invalid value"

            # Case 3: Direct string or other primitive
            return str(value)

        return process(serializer_errors)

    @staticmethod
    def get_first_error_message(errors):
        """
        Recursively extracts ONLY the first human-readable string message.
        Always returns a string or None.
        """
        # Case 1: Handle List
        if isinstance(errors, list):
            for item in errors:
                message = SerializerErrorHandler.get_first_error_message(item)
                if message:
                    return message

        # Case 2: Handle Dict
        elif isinstance(errors, dict):
            for value in errors.values():
                message = SerializerErrorHandler.get_first_error_message(value)
                if message:
                    return message

        # Case 3: Handle Primitive / ErrorDetail
        # DRF ErrorDetail acts like a string but is an object
        elif errors is not None:
            return str(errors)

        return None