from django.http import JsonResponse

def getRoutes(request): #view to show us all the routes in our api
    routes = [ 
        'GET /api',
        'GET /api/rooms', #Allows user to get all the rooms from our route
        'GET /api/rooms/:id' #Allows user to get a single room from our route
    ]
    return JsonResponse(routes, safe=False) #safe is going to allow this list to be turned into a JSON list data