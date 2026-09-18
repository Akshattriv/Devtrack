import json
import os

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from .entities import Reporter, build_issue
from issues.models import Reporter, Issue, CriticalIssue, LowPriorityIssue

REPORTERS_FILE = 'reporters.json'
ISSUES_FILE = 'issues.json'

def _load_data(file_path):
    if not os.path.exists(file_path):
        with open(file_path, 'w') as f:
            json.dump([], f)
        return []
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []


def _save_data(file_path, data):
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)

@csrf_exempt
def reporters_view(request):
    if request.method == 'GET':
        reporters = _load_data(REPORTERS_FILE)
        reporter_id = request.GET.get('id')

        if reporter_id is not None:
            try:
                target_id = int(reporter_id)
            except ValueError:
                return JsonResponse({'error': 'Query param id must be an integer'}, status=400)

            for r in reporters:
                if r.get('id') == target_id:
                    return JsonResponse(r, status=200)
            return JsonResponse({'error': 'Reporter not found'}, status=404)
        # If no id query param is provided, return all reporters
        return JsonResponse(reporters, safe=False, status=200)
    
    elif request.method == 'POST':
        try:
            payload = json.loads(request.body.decode('utf-8'))
        except (ValueError, TypeError, json.JSONDecodeError):
            return JsonResponse({'error': 'Invalid JSON body'}, status=400)

        reporter = Reporter(
            id=payload.get('id'),
            name=payload.get('name'),
            email=payload.get('email'),
            team=payload.get('team')
        )

        try:
            reporter.validate()
        except ValueError as err:
            return JsonResponse({'error': str(err)}, status=400)

        reporters = _load_data(REPORTERS_FILE)

        for r in reporters:
            if r.get('id') == reporter.id:
                return JsonResponse({'error': f'Reporter with ID {reporter.id} already exists'}, status=400)

        record = reporter.to_dict()
        reporters.append(record)
        _save_data(REPORTERS_FILE, reporters)
        return JsonResponse(record, status=201)
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def issues_view(request):
    if request.method == 'GET':
        issues = _load_data(ISSUES_FILE)
        issue_id = request.GET.get('id')
        issue_status = request.GET.get('status')

        if issue_id is not None:
            try:
                target_id = int(issue_id)
            except ValueError:
                return JsonResponse({'error': 'Query param id must be an integer'}, status=400)

            for i in issues:
                if i.get('id') == target_id:
                    return JsonResponse(i, status=200)
            return JsonResponse({'error': 'Issue not found'}, status=404)

        if issue_status is not None:
            try:
                target_status = str(issue_status)
            except ValueError:
                return JsonResponse({'error': 'Query param status must be a string'}, status=400)

            for i in issues:
                if i.get('status') == target_status:
                    return JsonResponse(i, status=200)
            return JsonResponse({'error': 'Issue not found'}, status=404)
        # If no id query param is provided, return all issues
        return JsonResponse(issues, safe=False, status=200)

    elif request.method == 'POST':
        try:
            payload = json.loads(request.body.decode('utf-8'))
        except json.JSONDecodeError as e:
            # This prints the exact error and where it happened to your console
            print(f"--- JSON Decode Error ---")
            print(f"Error Message: {e.msg}")
            print(f"Line: {e.lineno}, Column: {e.colno}")
            print(f"Raw Request Body: {request.body}")
            print(f"-------------------------")

        priority = payload.get('priority')
        params = {
            'id': payload.get('id'),
            'title': payload.get('title'),
            'description': payload.get('description'),
            'status': payload.get('status'),
            'priority': priority,
            'reporter_id': payload.get('reporter_id'),
            'created_at': payload.get('created_at')
        }

        # Subclass factory selection
        if priority == 'critical':
            issue = CriticalIssue(**params)
        elif priority == 'low':
            issue = LowPriorityIssue(**params)
        else:
            issue = Issue(**params)

        try:
            issue.validate()
        except ValueError as err:
            return JsonResponse({'error': str(err)}, status=400)

        issues = _load_data(ISSUES_FILE)

        for i in issues:
            if i.get('id') == issue.id:
                return JsonResponse({'error': f'Issue with ID {issue.id} already exists'}, status=400)

        issue_dict = issue.to_dict()
        issues.append(issue_dict)
        _save_data(ISSUES_FILE, issues)

        response_data = dict(issue_dict)
        response_data['message'] = issue.describe()
        return JsonResponse(response_data, status=201)
    return JsonResponse({'error': 'Method not allowed'}, status=405)