from django.urls import path

from complaint_box.views.client_views import (RegisterComplain, TripList, ClientComplaintList,
                                              ClientComplaintDetail)
from complaint_box.views.title_views import (GetAllTitles, GetAllReportSubcategories, GetAllLostAndFoundSubcategories,

                                        )
from complaint_box.views.administration_views import (AdministratorComplaintList,AdministratorComplaintDetail,
                                                      AdministratorComplaintRemark,
                                                    )
urlpatterns = [
    path("complaint-box/trip-list/", TripList.as_view()),

    path("client/register-complain/", RegisterComplain.as_view(),),
    path("client/complaint-list/", ClientComplaintList.as_view(),),
    path("client/complaint-detail/<uuid:complaint_id>/", ClientComplaintDetail.as_view(),),




    path("administrator/complaint-list/", AdministratorComplaintList.as_view(),),
    path("administrator/complaint-detail/<uuid:complaint_id>/", AdministratorComplaintDetail.as_view(),),

    path("administrator/complaint/<uuid:complaint_id>/remark/", AdministratorComplaintRemark.as_view(),),






    path("complaint-box/titles/", GetAllTitles.as_view(), name="get-all-titles"),
    path("complaint-box/report-subcategories/", GetAllReportSubcategories.as_view()),
    path("complaint-box/lost-and-found-subcategories/", GetAllLostAndFoundSubcategories.as_view()),

]

    

