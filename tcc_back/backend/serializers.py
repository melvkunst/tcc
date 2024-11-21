from rest_framework import serializers
from .models import Paciente, Exame, Alelo, ExameAlelo, Crossmatch, CrossmatchPatientResult, CrossmatchAlleleResult
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "password", "first_name", "last_name"]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        print(validated_data)
        user = User.objects.create_user(**validated_data)
        return user


class PacienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Paciente
        fields = ['id', 'nome', 'data_nascimento', 'tipo_sanguineo']

class ExameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exame
        fields = ['id', 'paciente_id', 'data_exame']

class AleloSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alelo
        fields = ['id', 'nome', 'numero1', 'numero2', 'tipo']

class ExameAleloSerializer(serializers.ModelSerializer):
    alelo = AleloSerializer()  # Inclui os detalhes do alelo

    class Meta:
        model = ExameAlelo
        fields = ['id', 'alelo', 'valor']


class CrossmatchAlleleResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = CrossmatchAlleleResult
        fields = ['allele_name', 'allele_value', 'compatibility']


class CrossmatchPatientResultSerializer(serializers.ModelSerializer):
    allele_results = CrossmatchAlleleResultSerializer(many=True, read_only=True)

    class Meta:
        model = CrossmatchPatientResult
        fields = ['patient_id', 'patient_name', 'total_compatible_alleles', 'total_incompatible_alleles', 'allele_results']


class CrossmatchSerializer(serializers.ModelSerializer):
    patient_results = CrossmatchPatientResultSerializer(many=True, read_only=True)

    class Meta:
        model = Crossmatch
        fields = ['id', 'donor_id', 'donor_name', 'donor_sex', 'donor_birth_date', 'donor_blood_type', 'date_performed', 'patient_results']
