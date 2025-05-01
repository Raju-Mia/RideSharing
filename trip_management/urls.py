from django.urls import path
from trip_management.views.client_views import (TripRequest, TripListForClient, TripDetailForClient,)
from trip_management.views.driver_views import (DriverTripAccept, DriverTripStatusUpdate, TripDelete, 
                                                DriverDeclineTrip, TakeTripBreak, TripAddExtraCharge, TripListForDriver,
                                                TripDetailForDriver,CompletedTripDetailForDriver,
                                                DeclineTripListByDriverAPIView,TripCancelByDriver,CancelTripList,TripSummary,
                                                CancellationReasonsView,EndTripBreak,DeclineTripListBySystemAPIView)
from trip_management.views.administrations_views import (BookingFeeScheduleListCreateView, UpdateBookingFeeSchedule,
                                                         CurrentBookingFee,DeleteBookingFeeSchedule,

                                                         )
from trip_management.views import one_way_trip_views                                            

#app name
app_name = 'trip_management'



urlpatterns = [
    # for passenger
    path('trip-request/', TripRequest.as_view()),
    path('delete/trip/by-user/<uuid:trip_id>/', TripDelete.as_view()),
    path('client/my-trips/', TripListForClient.as_view()),
    path('client/my-trip/<uuid:trip_id>/', TripDetailForClient.as_view()),

    # one way trip
    path('one-way-trip-fare/', one_way_trip_views.OneWayTripFareCalculation.as_view()),
    path('one-way-trip-request/', one_way_trip_views.OneWayTripRequest.as_view()),


    # for driver
    path('driver/accept/trip/<uuid:trip_id>/', DriverTripAccept.as_view()),
    path('driver/decline/trip/<uuid:trip_id>/',DriverDeclineTrip.as_view()),
    path('driver/trip/update-status/<uuid:trip_id>/', DriverTripStatusUpdate.as_view()),


    path('driver/trip-break/<uuid:trip_id>/', TakeTripBreak.as_view()),
    path('driver/trip-break/<uuid:trip_id>/<str:break_id>/', EndTripBreak.as_view()),

    path('driver/trip/add-extra-charge/<uuid:trip_id>/', TripAddExtraCharge.as_view()),

    path('driver/my-trips/', TripListForDriver.as_view()),
    path('driver/my-trip/<uuid:trip_id>/', TripDetailForDriver.as_view()),
    path('driver/completed-trip/<uuid:trip_id>/', CompletedTripDetailForDriver.as_view()),
    path('driver/trip-cancel/<uuid:trip_id>/', TripCancelByDriver.as_view()),
    path('driver/canceled-trip-list/',CancelTripList.as_view()),
    path('driver/decline-trip-list/', DeclineTripListByDriverAPIView.as_view()),
    path('driver/missed-trip-list/', DeclineTripListBySystemAPIView.as_view()),
    path('driver/trip-summary/<uuid:trip_id>/',TripSummary.as_view()),
    path('driver/cancellation-reasons/', CancellationReasonsView.as_view(),),



    # For administration
    path('administrator/manage-booking-fees/', BookingFeeScheduleListCreateView.as_view()),
    path('administrator/update-booking-fees/<int:instance_id>/', UpdateBookingFeeSchedule.as_view()),
    path('administrator/delete-booking-fees/<int:instance_id>/', DeleteBookingFeeSchedule.as_view()),
    path('administrator/current-booking-fees/', CurrentBookingFee.as_view()),








]
