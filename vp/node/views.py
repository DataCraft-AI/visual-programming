from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


from pyworkflow import Workflow, WorkflowException, Node, NodeException, node_factory
from rest_framework.decorators import api_view

from drf_yasg.utils import swagger_auto_schema


@swagger_auto_schema(method='post', operation_summary='Retrive a node from the graph', operation_description='Retrieves a node from the graph.', responses={200:'Node added to graph', 400: 'Node with id already exists in graph', 404:'Node/graph not found'})
@api_view(['POST'])
@csrf_exempt
def node(request):
    """ Add new Node to graph

    Adds a new node with specified data to the graph.

    Returns:
        200 - New Node was added to the graph
        400 - Missing info; Node with 'id' already exists in the graph
        404 - Graph or Node does not exist
        405 - Method not allowed
    """
    if request.method != 'POST':
        return JsonResponse({
            'message': 'Only POST requests are allowed.'
        }, status=405)

    # Load workflow from session
    workflow = Workflow.from_session(request.session)
    # Check if a graph is present
    if workflow.graph is None:
        return JsonResponse({
            'message': 'A workflow has not been created yet.'
        }, status=404)

    # Extract request info for node creation
    new_node = create_node(request)

    # If None, create_node failed
    if new_node is None:
        return JsonResponse({
            'message': 'Missing required Node information'
        }, status=400)

    # Check node_id is unique in graph
    if workflow.get_node(new_node.node_id) is not None:
        return JsonResponse({
            'message': 'A node with id %s already exists in the graph.' % new_node.node_id
        }, status=400)

    # Add Node to graph and re-save workflow to session
    workflow.add_node(new_node)
    request.session.update(workflow.to_session_dict())

    return JsonResponse({
        'message': 'Added new node to graph with id: %s' % (new_node.node_id)
    })

@swagger_auto_schema(method='post', operation_summary='Retrive a node from the graph', operation_description='Retrieves a node from the graph.', responses={200:'Added edge to graph', 404:'Workflow not created yet/Workflow does not contain specified node'})
@api_view(['POST'])
def edge(request, node_from_id, node_to_id):
    """ Add new edge to the graph

        Creates a new edge from node_from_id to node_to_id.
    """
    # Load workflow from session
    workflow = Workflow.from_session(request.session)
    # Check if a graph is present
    if workflow.graph is None:
        return JsonResponse({
            'message': 'A workflow has not been created yet.'
        }, status=404)

    # Check if the graph contains the requested Node
    node_from = workflow.get_node(node_from_id)
    node_to = workflow.get_node(node_to_id)

    if node_from is None or node_to is None:
        return JsonResponse({
            'message': 'The workflow does not contain the node(s) requested.'
        }, status=404)

    # Add Edge between the Nodes to the graph and re-save workflow to session
    workflow.add_edge(node_from, node_to)
    request.session.update(workflow.to_session_dict())

    return JsonResponse({
        'message': 'Added new edge to graph from node %s to node %s' %
                   (node_from.node_id, node_to.node_id)
    })


@swagger_auto_schema(method='get', operation_summary='Retrive a node from the graph', operation_description='Retrieves a node from the graph.', responses={200:'JSON response with data', 400: 'No file specified', 404:'Node/graph not found'})
@swagger_auto_schema(method='delete', operation_summary='Delete a node from the graph', operation_description='Deletes a node from the graph.', responses={200:'JSON response with data', 400: 'No file specified', 404:'Node/graph not found', 405:'Method not allowed', 500:'Error processing Node change'})
@api_view(['GET', 'DELETE'])
@csrf_exempt
def handle_node(request, node_id):
    """ Retrieve/delete a Node from the graph

    Returns:
        200 - Node was found; data in JSON format
        404 - Graph or Node does not exist
        405 - Method not allowed
        500 - Error processing Node change
    """

    # Load workflow from session
    workflow = Workflow.from_session(request.session)
    # Check if a graph is present
    if workflow.graph is None:
        return JsonResponse({
            'message': 'A workflow has not been created yet.'
        }, status=404)

    # Check if the graph contains the requested Node
    node = workflow.get_node(node_id)

    if node is None:
        return JsonResponse({
            'message': 'The workflow does not contain node id ' + str(node_id)
        }, status=404)

    # Process request
    try:
        if request.method == 'GET':
            # Node class is not JSON serializable, so pass in __dict__
            response = JsonResponse(node.__dict__, safe=False)
        elif request.method == 'DELETE':
            workflow.remove_node(node)
            response = JsonResponse({
                'message': 'Removed node ID #' + str(node.node_id)
            })
        else:
            return JsonResponse({
                'message': request.method + ' not yet handled.'
            }, status=405)
    except WorkflowException as e:
        return JsonResponse(e, status=500)

    # Save any changes back to session
    request.session.update(workflow.to_session_dict())
    return response


def execute_node(request, node_id):
    """Execute the specified node

    """
    # Load workflow from session
    workflow = Workflow.from_session(request.session)

    # Check if the graph contains the requested Node
    node_to_execute = workflow.get_node(node_id)

    if node_to_execute is None:
        return JsonResponse({
            'message': 'The workflow does not contain node id ' + str(node_id)
        }, status=404)

    # Execute node
    try:
        node_to_execute.execute()
        return JsonResponse({
            'message': 'Node Execution successful!',
            'node_type': node_to_execute.node_type,
            'data': node_to_execute.data,
        }, safe=False)
    except NodeException as e:
        return JsonResponse({e.action: e.reason}, status=500)


def create_node(request):
    """Pass all request info to Node Factory.

    """
    try:
        return node_factory(request.POST)
    except OSError as e:
        return JsonResponse({'message': e.strerror}, status=404)
    except NodeException as e:
        return JsonResponse({e.action: e.reason}, status=400)
