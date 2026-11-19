
def add_task_constraints(model, candidates, task_vars):
    """
    A maintenance task can be selected at most once.
    """

    task_groups = {}

    for i, candidate in enumerate(candidates):
        task_id = candidate["task_id"]
        task_groups.setdefault(task_id, []).append(task_vars[i])

    for task_id, variables in task_groups.items():
        model.Add(sum(variables) <= 1)


def add_block_constraints(model, candidates, intervals):
    """
    Tasks assigned to the same block cannot overlap.
    """

    block_groups = {}

    for i, candidate in enumerate(candidates):
        block_id = candidate["block_window_id"]
        block_groups.setdefault(block_id, []).append(intervals[i])

    for block_id, block_intervals in block_groups.items():

        if len(block_intervals) > 1:
            model.AddNoOverlap(block_intervals)
