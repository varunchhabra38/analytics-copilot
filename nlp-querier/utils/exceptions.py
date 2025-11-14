class DatabaseError(Exception):
    """Exception raised for errors in the database operations."""
    pass

class SQLExecutionError(Exception):
    """Exception raised for errors during SQL execution."""
    pass

class SQLValidationError(Exception):
    """Exception raised for errors in SQL validation."""
    pass

class SchemaLookupError(Exception):
    """Exception raised for errors in schema lookup."""
    pass

class ClarificationNeededError(Exception):
    """Exception raised when clarification is needed from the user."""
    pass

class VisualizationError(Exception):
    """Exception raised for errors in visualization generation."""
    pass

class SummaryGenerationError(Exception):
    """Exception raised for errors in summary generation."""
    pass