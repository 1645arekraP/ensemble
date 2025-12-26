from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets
from apps.graph.models import Graph 
from apps.graph.services.runner import GraphRunner 
from .serializers import RunInputSerializer, ExecutionLogSerializer
from .models import ExecutionLog

class ProjectRunView(APIView):
    """
    Handles the execution of a saved project graph.
    """
    def post(self, request, project_id):
        # Validate the incoming input
        serializer = RunInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        user_input = serializer.validated_data['input']

        # Get the saved graph
        try:
            graph = Graph.objects.get(id=project_id, owner=request.user) 
        except Graph.DoesNotExist:
            return Response({"error": "Graph project not found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            # Instantiate GraphRunner and call run_graph
            runner = GraphRunner()
            result = runner.run_graph(
                graph=graph, 
                initial_input=user_input,
                user=request.user 
            )
            
            # Return the final result
            if result.get('success'):
                return Response(result, status=status.HTTP_200_OK)
            else:
                # If GraphRunner handled the error, return its response
                return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            # Log the full exception here
            print(f"Error running graph view: {e}")
            # This is for unexpected errors in the view itself
            return Response({"success": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ExecutionLogViewSet(viewsets.ModelViewSet):
    serializer_class = ExecutionLogSerializer
    http_method_names = ['get', 'delete', 'head', 'options']

    def get_queryset(self):
        return ExecutionLog.objects.filter(user=self.request.user).order_by('-started_at')

    def filter_queryset(self, queryset):
        graph_id = self.request.query_params.get('graph_id')
        if graph_id:
            return queryset.filter(graph_id=graph_id)
        return queryset