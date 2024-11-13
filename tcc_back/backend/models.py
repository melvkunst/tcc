from django.db import models

class Paciente(models.Model):
    id = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=255)  # Ajuste o tamanho conforme necessário
    data_nascimento = models.DateField()
    tipo_sanguineo = models.CharField(max_length=3)  # Para tipos como 'A+', 'O-', etc.

    class Meta:
        db_table = 'pacientes'  # Nome da tabela no banco de dados

    def __str__(self):
        return self.nome

class Exame(models.Model):
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='exames')
    data_exame = models.DateField()

    class Meta:
        db_table = 'exames'  # Nome da tabela para exames

    def __str__(self):
        return f"Exame {self.id} - Paciente {self.paciente_id} - Data {self.data_exame}"

class Alelo(models.Model):
    nome = models.CharField(max_length=100)
    numero1 = models.IntegerField()
    numero2 = models.IntegerField()
    tipo = models.CharField(max_length=2)

    class Meta:
        db_table = 'alelos'

class ExameAlelo(models.Model):
    exame = models.ForeignKey(Exame, on_delete=models.CASCADE, related_name='exames_alelos')
    alelo = models.ForeignKey(Alelo, on_delete=models.CASCADE, related_name='alelos')
    valor = models.FloatField()

    class Meta:
        db_table = 'exames_alelos'


class Crossmatch(models.Model):
    donor_id = models.IntegerField()
    donor_name = models.CharField(max_length=100)
    donor_sex = models.CharField(max_length=10)
    donor_birth_date = models.DateField()
    donor_blood_type = models.CharField(max_length=3)
    date_performed = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'crossmatch'  # Nome da tabela existente no banco de dados

    def __str__(self):
        return f"Crossmatch {self.id} - Doador: {self.donor_name}"


class CrossmatchPatientResult(models.Model):
    crossmatch = models.ForeignKey(Crossmatch, on_delete=models.CASCADE, related_name='patient_results')
    patient_id = models.IntegerField()
    patient_name = models.CharField(max_length=100)
    total_compatible_alleles = models.IntegerField()
    total_incompatible_alleles = models.IntegerField()

    class Meta:
        db_table = 'crossmatchpatientresult'  # Nome da tabela existente no banco de dados

    def __str__(self):
        return f"Resultado do Paciente {self.patient_name} para Crossmatch {self.crossmatch.id}"


class CrossmatchAlleleResult(models.Model):
    patient_result = models.ForeignKey(CrossmatchPatientResult, on_delete=models.CASCADE, related_name='allele_results')
    allele_name = models.CharField(max_length=10)
    allele_value = models.FloatField()
    compatibility = models.BooleanField()

    class Meta:
        db_table = 'crossmatchalleleresult'  # Nome da tabela existente no banco de dados

    def __str__(self):
        return f"Alelo {self.allele_name} - Compatível: {self.compatibility}"