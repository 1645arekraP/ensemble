from rest_framework import serializers

class RunInputSerializer(serializers.Serializer):
    """
    Serializes the input for a graph run.
    This just validates the POST data from the user.
    """
    input = serializers.CharField(
        required=True,
        allow_blank=False,
        help_text="The user's initial input message to start the graph execution."
    )