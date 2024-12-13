from rest_framework import serializers
from .models import UserProfile, SaaSPlan, Document

class SaaSPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SaaSPlan
        fields = ['id', 'name', 'max_storage_mb', 'price', 'max_queries', 'max_documents']

class UserProfileSerializer(serializers.ModelSerializer):
    saas_plan = SaaSPlanSerializer(read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    total_credits = serializers.SerializerMethodField()  # Custom field for sum of credits
    plan_start_date = serializers.SerializerMethodField()  # Custom field for formatted date
    plan_end_date = serializers.SerializerMethodField()    # Custom field for formatted date
    credits = serializers.SerializerMethodField()          # Custom field for integer credits
    recharged_credits = serializers.SerializerMethodField()  # Custom field for integer recharged credits

    class Meta:
        model = UserProfile
        fields = [
            'user', 'username', 'user_email', 'credits', 'recharged_credits', 'total_credits',
            'saas_plan', 'plan_start_date', 'plan_end_date', 'is_plan_active', 'total_documents_uploaded'
        ]

    def get_total_credits(self, obj):
        # Calculate the sum of credits and recharged_credits
        return int(obj.credits + obj.recharged_credits)

    def get_plan_start_date(self, obj):
        # Format plan_start_date to dd-mm-yyyy
        return obj.plan_start_date.strftime('%d-%m-%Y') if obj.plan_start_date else None

    def get_plan_end_date(self, obj):
        # Format plan_end_date to dd-mm-yyyy
        return obj.plan_end_date.strftime('%d-%m-%Y') if obj.plan_end_date else None

    def get_credits(self, obj):
        # Return credits as an integer
        return int(obj.credits)

    def get_recharged_credits(self, obj):
        # Return recharged_credits as an integer
        return int(obj.recharged_credits)

class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = '__all__'  # Include all relevant fields
