import json
import csv

from django.http import JsonResponse, HttpResponse
from django.conf import settings
from django.core.files.storage import FileSystemStorage
import networkx as nx

from pyworkflow import Workflow, WorkflowException


fs = FileSystemStorage(location=settings.MEDIA_ROOT)


def new_workflow(request):
    """ Create a new workflow.

    Initialize a new, empty, NetworkX DiGraph object and store it in
    the session

    Return:
        200 - Created new DiGraph
    """
    # Create new NetworkX graph
    DG = nx.DiGraph()
    json_graph = nx.readwrite.json_graph.node_link_data(DG)

    # Construct response
    data = {
        'graph': json_graph,
        'nodes': DG.number_of_nodes(),
    }

    # Save to session
    request.session['graph'] = json_graph
    return JsonResponse(data)


def open_workflow(request):
    """Opens a workflow.

    If file is specified in GET request, that file is opened.

    Args:
        request: Django request Object

    Returns:
        200 - JSON response with data.
        400 - No file specified
        404 - File specified not found, or not JSON graph
    """
    # If file included in request, extract it
    file_path = request.GET.get('file')
    if file_path is None:
        return JsonResponse({'message': 'File must be specified.'}, status=400)

    # Read info into Workflow object
    try:
        with fs.open(file_path) as file_like:
            workflow = Workflow.from_file(file_like)
    except OSError as e:
        return JsonResponse({'message': e.strerror}, status=404)
    except nx.NetworkXError as e:
        return JsonResponse({'message': str(e)}, status=404)
    except WorkflowException as e:
        return JsonResponse({e.action: e.reason}, status=404)

    # Construct response
    data = {
        'graph': workflow.to_graph_json(),
        'nodes': workflow.graph.number_of_nodes(),
    }

    # Save Workflow info to session
    request.session.update(workflow.to_session_dict())
    return JsonResponse(data)


def save_workflow(request):
    """Saves a workflow to disk.

    Args:
        request: Django request Object

    Returns:
        Downloads JSON file representing graph.
    """
    # Check session for existing graph
    if request.session.get('graph') is None:
        return JsonResponse({'message': 'No graph exists.'}, status=404)

    # Load session data into Workflow object. If successful, return
    # serialized graph
    try:
        workflow = Workflow.from_session(request.session)
        json_str = json.dumps(workflow.to_graph_json())
        response = HttpResponse(json_str, content_type='application/json')
        response['Content-Disposition'] = 'attachment; filename=%s' % workflow.file_path
        return response
    except WorkflowException as e:
        return JsonResponse({e.action: e.reason}, status=404)


def retrieve_nodes_for_user(request):
    if request.method == 'GET':
        """
        Retrieve all nodes that a user can have access to in the IDE.
        Currently returning default set of nodes. 
        //TODO pick these node files from a file in the system.
        """
        data = {
            "I/O": [
                {"key": "read-csv", "name": "Read CSV", "numPortsIn": 0, "color": "black"}
            ],
            "Manipulation": [
                {"key": "filter", "name": "Filter Rows", "color": "red"},
                {"key": "pivot", "name": "Pivot Table", "color": "blue"},
                {"key": "multi-in", "name": "Multi-Input Example", "numPortsIn": 3, "color": "green"}
            ]
        }
        return JsonResponse(data, safe=False, status=200)


def retrieve_csv(request, node_id):
    if request.method == 'GET':
        """
        Retrieves a CSV after the associated node execution and returns it as a json.
        Currently just using a demo CSV in workspace. 
        """
        # Create the HttpResponse object with the appropriate CSV header.
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="somefilename.csv"'

        writer = csv.writer(response)
        writer.writerow(['First row', 'Foo', 'Bar', 'Baz'])
        writer.writerow(['Second row', 'A', 'B', 'C', '"Testing"', "Here's a quote"])

        return response
