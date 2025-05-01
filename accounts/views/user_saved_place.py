from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.response import Response
from accounts.models import SavedPlace
from accounts.serializers import SavedPlaceSerializer
from rest_framework.generics import get_object_or_404
from utils.pagination import CustomPageNumberPagination








class SavedPlaceListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        saved_places = SavedPlace.objects.filter(user=request.user)
        
        paginator = CustomPageNumberPagination()
        paginated_places = paginator.paginate_queryset(saved_places, request)
        
        if paginated_places is not None:
            serializer = SavedPlaceSerializer(paginated_places, many=True)
            return paginator.get_paginated_response(serializer.data)
        return paginator.get_paginated_response([])
    def post(self, request):
        serializer = SavedPlaceSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class SavedPlaceDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        return get_object_or_404(SavedPlace, pk=pk, user=self.request.user)

    def get(self, request, pk):
        saved_place = self.get_object(pk)
        serializer = SavedPlaceSerializer(saved_place)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        saved_place = self.get_object(pk)
        data = request.data.copy()
        data['user'] = request.user.id  # Ensure user cannot be modified
        serializer = SavedPlaceSerializer(saved_place, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        saved_place = self.get_object(pk)
        saved_place.delete()
        return Response({"message": "Saved place deleted."}, status=status.HTTP_204_NO_CONTENT)