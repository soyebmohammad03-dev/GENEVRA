"""Example entrant using proportional independent units under the frozen tariff."""


def allocate(request):
    high = round(
        request.budget
        * request.weights[1]
        / sum(c * w for c, w in zip(request.costs, request.weights, strict=True))
    )
    upper = (request.budget - request.costs[0] * request.minimum) // request.costs[1]
    high = min(upper, max(request.minimum, high))
    low = (request.budget - request.costs[1] * high) // request.costs[0]
    return low, high
