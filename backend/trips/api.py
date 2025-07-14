from rest_framework.response import Response
from .models import Trip
from .serializers import TripSerializer
from rest_framework import generics
from .permissions import IsManager
from rest_framework.permissions import (
    IsAuthenticated,
    IsAdminUser,
)

from rest_framework.decorators import api_view


@api_view(['GET'])
def api_overview(request):
     
	api_urls = {

        'auth api overview' : '/',
        'list and create new trip' : 'create/',
        'Update, retreive and delete a trip' : 'detail/<int:pk>/',
		}

	return Response(api_urls)


class TripListView(generics.ListCreateAPIView):
    queryset = Trip.objects.all()
    serializer_class = TripSerializer
    permission_classes = [ IsAuthenticated]



class TripDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Trip.objects.all()
    serializer_class = TripSerializer
    permission_classes = [IsManager, IsAdminUser, IsAuthenticated]

