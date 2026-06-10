from rest_framework import serializers
from .models import User, Profile

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)

    department_name = serializers.CharField(source='department.name', read_only=True)
    semester = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'role', 'is_hod', 'phone_number', 'department', 'department_name', 'year', 'batch', 'semester', 'first_name', 'last_name')

    def get_semester(self, obj):
        return 2 * obj.year - 1 # Simple mapping for demo

    def create(self, validated_data):
        password = validated_data.pop('password', 'pjpcollege123')
        # Use create_user for proper handling of AbstractUser
        user = User.objects.create_user(password=password, **validated_data)
        return user

    def validate_username(self, value):
        # Exclude self during updates to avoid false uniqueness violations
        qs = User.objects.filter(username=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return value

    def validate_email(self, value):
        # Exclude self during updates to avoid false uniqueness violations
        qs = User.objects.filter(email=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if value and qs.exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Profile
        fields = '__all__'

    def update(self, instance, validated_data):
        user_data = self.context['request'].data.get('user')
        if user_data:
            user = instance.user
            if 'first_name' in user_data:
                user.first_name = user_data['first_name']
            if 'last_name' in user_data:
                user.last_name = user_data['last_name']
            if 'email' in user_data:
                user.email = user_data['email']
            if 'phone_number' in user_data:
                user.phone_number = user_data['phone_number']
            if 'password' in user_data and user_data['password']:
                user.set_password(user_data['password'])
            user.save()
            
        return super().update(instance, validated_data)
