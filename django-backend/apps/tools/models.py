from django.db import models

class Tool(models.Model):
    """
    Defines a tool that an agent can use. The actual Python function is implemented
    separately in your agent logic.
    """
    name = models.CharField(max_length=100, unique=True, help_text="The function name for the tool.")
    description = models.TextField(help_text="Description for the LLM to understand the tool's purpose.")

    def __str__(self):
        return self.name