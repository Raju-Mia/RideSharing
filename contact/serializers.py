# contact serializer
from rest_framework import serializers
from .models import Contact, Newsletter, ComplaintBox

TITLE = (
    ("custom", "Custom"),
    ("late arrival", "Late Arrival"),
    ("unsafe driving concerns", "Unsafe Driving Concerns"),
    ("rude and unprofessional conduct", "Rude and Unprofessional Conduct"),
    ("vehicle cleanliness complaints", "Vehicle Cleanliness Complaints"),
    ("vehicle condition issues", "Vehicle Condition Issues"),
    ("navigation problems", "Navigation Problems"),
    ("inadequate knowledge", "Inadequate Knowledge"),
    ("communication challenges", "Communication Challenges"),
    ("overcharging disputes", "Overcharging Disputes"),
    ("misbehavior and harassment", "Misbehavior and Harassment"),
    ("amenities promise", "Amenities Promise"),
    ("last minute cancellations", "Last Minute Cancellations"),
    ("billing hiccups", "Billing Hiccups"),
    ("chauffeur no show", "Chauffeur No Show"),
    ("lost or damaged belongings", "Lost or Damaged Belongings"),
    ("impatient behavior", "Impatient Behavior"),
    ("excessive stops", "Excessive Stops"),
    ("messy vehicle", "Messy Vehicle"),
    ("lack of gratuity", "Lack of Gratuity"),
    ("frequent route changes", "Frequent Route Changes"),
    ("imprecise directions", "Imprecise Directions"),
    ("overloading", "Overloading"),
    ("inconsiderate behavior", "Inconsiderate Behavior"),
    ("unauthorized stops", "Unauthorized Stops"),
    ("extended wait times", "Extended Wait Times"),
    ("client no show", "Client No Show"),
    ("incorrect address", "Incorrect Address"),
    ("unwarranted criticism", "Unwarranted Criticism"),
    ("unpaid fees", "Unpaid Fees"),
)


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = "__all__"


class NewsletterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Newsletter
        fields = "__all__"


class ComplaintBoxSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComplaintBox
        fields = "__all__"


class CreateComplaintBoxSerializer(serializers.ModelSerializer):
    choice = serializers.ChoiceField(choices=TITLE, required=False)
    title = serializers.CharField()

    class Meta:
        model = ComplaintBox
        fields = ["user", "trip", "choice", "title", "issue"]

    def validate(self, data):
        choice = data.get("choice", None)
        title = data.get("title", None)

        if choice is None and title is None:
            raise serializers.ValidationError(
                "Either 'choice' or 'title' is required, but not both."
            )

        if choice is not None and title is not None:
            raise serializers.ValidationError(
                "Only one of 'choice' or 'title' can be provided, not both."
            )

        return data

    def create(self, validated_data):
        choice = validated_data.get("choice")
        title = validated_data.get("title")

        if choice is not None:
            validated_data["title"] = choice

        return super().create(validated_data)


class UpdateComplaintBoxSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComplaintBox
        fields = "__all__"
        read_only_fields = ["id", "user", "trip", "title", "created_at", "created_by"]
