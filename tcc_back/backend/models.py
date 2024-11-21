from django.utils.timezone import now
from django.db import models


# Modelo de pacientes
class Paciente(models.Model):
    id = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=255)  # Nome do paciente
    data_nascimento = models.DateField()  # Data de nascimento
    tipo_sanguineo = models.CharField(max_length=3)  # Tipo sanguíneo (ex.: 'A+', 'O-')

    class Meta:
        db_table = 'pacientes'  # Nome da tabela no banco de dados

    def __str__(self):
        return self.nome


# Modelo de exames
class Exame(models.Model):
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='exames')  # Relacionado ao paciente
    data_exame = models.DateField()  # Data do exame

    class Meta:
        db_table = 'exames'  # Nome da tabela no banco de dados

    def __str__(self):
        return f"Exame {self.id} - Paciente {self.paciente_id} - Data {self.data_exame}"


# Modelo de alelos
class Alelo(models.Model):
    nome = models.CharField(max_length=100)  # Nome do alelo (ex.: "A01:01")
    numero1 = models.IntegerField()  # Parte numérica 1
    numero2 = models.IntegerField()  # Parte numérica 2
    tipo = models.CharField(max_length=2)  # Tipo do alelo (ex.: 'A', 'B', etc.)

    class Meta:
        db_table = 'alelos'  # Nome da tabela no banco de dados

    def __str__(self):
        return self.nome


# Modelo para associação entre exames e alelos
class ExameAlelo(models.Model):
    exame = models.ForeignKey(Exame, on_delete=models.CASCADE, related_name='exames_alelos')  # Relacionado ao exame
    alelo = models.ForeignKey(Alelo, on_delete=models.CASCADE, related_name='alelos')  # Relacionado ao alelo
    valor = models.FloatField()  # Valor relacionado ao alelo no exame

    class Meta:
        db_table = 'exames_alelos'  # Nome da tabela no banco de dados


# Modelo para registros de Crossmatch
class Crossmatch(models.Model):
    donor_id = models.IntegerField()  # ID do doador
    donor_name = models.CharField(max_length=100)  # Nome do doador
    donor_sex = models.CharField(max_length=10)  # Sexo do doador
    donor_birth_date = models.DateField()  # Data de nascimento do doador
    donor_blood_type = models.CharField(max_length=3)  # Tipo sanguíneo do doador
    date_performed = models.DateTimeField(auto_now_add=True)  # Data em que o Crossmatch foi realizado

    class Meta:
        db_table = 'crossmatch'  # Nome da tabela no banco de dados

    def __str__(self):
        return f"Crossmatch {self.id} - Doador: {self.donor_name}"


# Modelo para resultados de pacientes em um Crossmatch
class CrossmatchPatientResult(models.Model):
    crossmatch = models.ForeignKey(Crossmatch, on_delete=models.CASCADE, related_name='patient_results')  # Relacionado ao Crossmatch
    patient_id = models.IntegerField()  # ID do paciente
    patient_name = models.CharField(max_length=100)  # Nome do paciente
    total_compatible_alleles = models.IntegerField()  # Total de alelos compatíveis
    total_incompatible_alleles = models.IntegerField()  # Total de alelos incompatíveis

    class Meta:
        db_table = 'crossmatchpatientresult'  # Nome da tabela no banco de dados

    def __str__(self):
        return f"Resultado do Paciente {self.patient_name} para Crossmatch {self.crossmatch.id}"


# Modelo para resultados de alelos em um paciente no Crossmatch
class CrossmatchAlleleResult(models.Model):
    patient_result = models.ForeignKey(CrossmatchPatientResult, on_delete=models.CASCADE, related_name='allele_results')  # Relacionado ao resultado do paciente
    allele_name = models.CharField(max_length=20)  # Nome do alelo
    allele_value = models.FloatField()  # Valor do alelo
    compatibility = models.BooleanField()  # Indica se o alelo é compatível

    class Meta:
        db_table = 'crossmatchalleleresult'  # Nome da tabela no banco de dados

    def __str__(self):
        return f"Alelo {self.allele_name} - Compatível: {self.compatibility}"
