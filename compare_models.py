import os
from clearml import Task


def get_clearml_task_of_current_commit(commit_id):
    """Find the ClearML task that correspond to the exact codebase in the commit ID."""
    # Get the ID and Diff of all tasks based on the current commit hash, order by newest
    tasks = Task.query_tasks(
        task_filter={
            'order_by': ['-last_update'],
            '_all_': dict(fields=['script.version_num'],
                          pattern=commit_id
                          ),
            'status': ['completed']
        },
        additional_return_fields=['script.diff']
    )

    # If there are tasks, check which one has no diff: aka which one was run with the exact
    # code that is staged in this PR.
    if tasks:
        for task in tasks:
            if not task['script.diff']:
                return Task.get_task(task_id=task['id'])

    # If no task was run yet with the exact PR code, raise an error and block the PR.
    raise ValueError("No task based on this code was found in ClearML."
                     "Make sure to run it at least once before merging.")


def compare_and_tag_task(commit_hash):
    """Compare current performance to best previous performance and only allow equal or better."""
    current_task = get_clearml_task_of_current_commit(commit_hash)
    best_task = Task.get_task(project_name='Github CICD Video', task_name='cicd_test', tags=['Best Performance'])
    if best_task:
        best_metric = max(
            best_task.get_reported_scalars().get('Performance Metric').get('Series 1').get('y')
        )
        current_metric = max(
            current_task.get_reported_scalars().get('Performance Metric').get('Series 1').get('y')
        )
        print(f"Best metric in the system is: {best_metric} and current metric is {current_metric}")
        if current_metric >= best_metric:
            print("This means current metric is better or equal! Tagging as such.")
            current_task.add_tags(['Best Performance'])
        else:
            print("This means current metric is worse! Not tagging.")
    else:
        current_task.add_tags(['Best Performance'])


if __name__ == '__main__':
    print(f"Running on commit hash: {os.getenv('COMMIT_ID')}")
    compare_and_tag_task(os.getenv('COMMIT_ID'))
