from rest_framework import serializers
from .models import BookingUser
from trips.models import Trip
from trips.serializers import TripSerializer
from django.utils import timezone
from django.db import models


class BookingSerializer(serializers.ModelSerializer):

    trip_details = TripSerializer(source='trip', read_only=True)
    user = serializers.StringRelatedField(read_only=True)
    total_price = serializers.SerializerMethodField()
    assigned_seats = serializers.SerializerMethodField()

    class Meta:
        model = BookingUser
        fields = [
            'id', 'user', 'trip', 'trip_details', 'booking_date',
            'number_of_seats', 'is_cancelled', 'cancellation_date',
            'total_price', 'assigned_seats', 'user_name', 'user_phone_number',
        ]
        read_only_fields = ['booking_date', 'cancellation_date'] 
        extra_kwargs = {
            'trip': {'write_only': True}
        }

    def get_total_price(self, obj):
        if hasattr(obj, 'total_price'):
            return obj.total_price
        if obj.trip and obj.number_of_seats is not None:
            return obj.trip.price * obj.number_of_seats
        return 0

    def validate(self, data):
        is_update = self.instance is not None
        
        if is_update and 'is_cancelled' in data and data['is_cancelled'] is True:
            if self.instance.is_cancelled:
                raise serializers.ValidationError("الحجز ملغى بالفعل ولا يمكن إلغاؤه مرة أخرى.")
            return data

        trip = data.get('trip')
        if is_update and not trip:
            trip = self.instance.trip
        
        if not trip:
            raise serializers.ValidationError({"trip": "Trip is required."})

        if trip.departure_date < timezone.now():
            raise serializers.ValidationError("لا يمكن حجز رحلة في الماضي.")

        number_of_seats = data.get('number_of_seats')
        if number_of_seats is None and is_update:
            number_of_seats = self.instance.number_of_seats

        if number_of_seats is None:
             raise serializers.ValidationError({"number_of_seats": "Number of seats is required."})

        if number_of_seats <= 0:
            raise serializers.ValidationError("Number of seats must be at least 1.")

        if number_of_seats > trip.available_seats:
            raise serializers.ValidationError(
                f"Only {trip.available_seats} seat(s) available."
            )
        
        user = self.context['request'].user
        if not is_update and BookingUser.objects.filter(user=user, trip=trip, is_cancelled=False).exists():
            raise serializers.ValidationError("لقد قمت بالفعل بحجز هذه الرحلة.")

        if number_of_seats > 5:
            raise serializers.ValidationError("لا يمكنك حجز أكثر من 5 مقاعد دفعة واحدة.")
        
        booked_seats = BookingUser.objects.filter(trip=trip, is_cancelled=False).aggregate(
            total = models.Sum('number_of_seats')
        )['total'] or 0

        if is_update:
            booked_seats -= self.instance.number_of_seats

        available_seats = trip.total_seats - booked_seats

        if number_of_seats > available_seats:
            raise serializers.ValidationError({
                'number_of_seats': f"فقط {available_seats} مقعد(مقاعد) متاح(ة) في هذه الرحلة."
            })

        return data
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
    
    def get_assigned_seats(self, obj):
        if not obj.pk:
            return []
            
        all_bookings = BookingUser.objects.filter(trip=obj.trip, is_cancelled=False).order_by('booking_date', 'id')

        assigned_seats = []
        current_seat = 1

        for booking in all_bookings:
            end_seat = current_seat + booking.number_of_seats - 1
            seat_range = list(range(current_seat, end_seat + 1))

            if booking.id == obj.id:
                assigned_seats = seat_range
                break 

            current_seat = end_seat + 1

        return assigned_seats