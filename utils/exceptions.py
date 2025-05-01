class BoundaryNotSet(Exception):
    def __init__(self, message="Boundaries are not set yet"):
        self.message = message
        super().__init__(self.message)
