# accounts/api_serializers.py
from django.contrib.auth import authenticate
from rest_framework import serializers

from .models import Article, Course, CustomUser, ResearchProject


class UserSerializer(serializers.ModelSerializer):
    is_admin = serializers.BooleanField(read_only=True)

    class Meta:
        model = CustomUser
        fields = [
            'id', 'email', 'phone', 'full_name', 'first_name', 'last_name',
            'avatar', 'role', 'is_admin', 'is_verified', 'bio', 'organization',
            'field_of_study', 'website', 'linkedin', 'google_scholar',
            'activity_logs_enabled',
        ]
        # email و phone read-only: تغییرشان نیاز به flow جدا با verification دارد
        read_only_fields = ['id', 'email', 'phone', 'role', 'is_admin', 'is_verified']


class SendOTPSerializer(serializers.Serializer):
    email_or_phone = serializers.CharField()

    def validate_email_or_phone(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('این فیلد الزامی است.')
        return value


class VerifyOTPSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    code = serializers.CharField(max_length=6, min_length=6)


class SignupSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    phone = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = CustomUser
        fields = ['email', 'phone', 'password']

    def validate_email(self, value):
        value = value.strip().lower()
        if CustomUser.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('این ایمیل قبلاً ثبت شده است.')
        return value

    def validate_phone(self, value):
        if not value:
            return None
        value = value.strip()
        if CustomUser.objects.filter(phone=value).exists():
            raise serializers.ValidationError('این شماره قبلاً ثبت شده است.')
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = CustomUser(**validated_data)
        user.set_password(password)
        user.is_active = False
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    identifier = serializers.CharField()  # ایمیل یا موبایل
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        request = self.context.get('request')
        identifier = attrs['identifier'].strip()
        # ← تغییر: همیشه username=identifier (backend خودش تشخیص می‌دهد)
        user = authenticate(request, username=identifier, password=attrs['password'])
        if user is None:
            raise serializers.ValidationError('اطلاعات وارد شده صحیح نیست.')
        if not user.is_active:
            raise serializers.ValidationError('حساب شما غیرفعال شده است.')
        attrs['user'] = user
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('رمز عبور فعلی نادرست است.')
        return value


class VerifyEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6, min_length=6)


class ResendCodeSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6, min_length=6)
    new_password = serializers.CharField(write_only=True, min_length=8)


class AdminUserSerializer(serializers.ModelSerializer):
    is_admin = serializers.BooleanField(read_only=True)

    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'phone', 'full_name', 'role', 'is_admin',
                  'is_active', 'is_verified', 'date_joined']
        read_only_fields = fields


class ArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = ['id', 'title', 'abstract', 'content', 'authors', 'created_by',
                  'status', 'created_at', 'updated_at', 'published_at']
        read_only_fields = ['created_by', 'created_at', 'updated_at']


class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ['id', 'title', 'description', 'teacher', 'students',
                  'start_date', 'end_date', 'is_active', 'created_at']


class ResearchProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResearchProject
        fields = ['id', 'title', 'description', 'lead', 'team_members', 'status',
                  'budget', 'start_date', 'end_date', 'created_at']