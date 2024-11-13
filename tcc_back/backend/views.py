from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import pandas as pd
from django.http import JsonResponse
from .models import Paciente, Exame, ExameAlelo, Alelo, Crossmatch, CrossmatchPatientResult, CrossmatchAlleleResult
from .serializers import PacienteSerializer, ExameSerializer, ExameAleloSerializer, CrossmatchSerializer, CrossmatchPatientResultSerializer, CrossmatchAlleleResultSerializer
from datetime import datetime

@api_view(['GET', 'POST'])
def lista_cria_pacientes(request):
    if request.method == 'GET':
        pacientes = Paciente.objects.all().order_by('nome')  # Ordena os pacientes em ordem alfabética
        serializer = PacienteSerializer(pacientes, many=True)
        return JsonResponse(serializer.data, safe=False, json_dumps_params={'ensure_ascii': False})
    elif request.method == 'POST':
        serializer = PacienteSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
def detalhe_paciente(request, paciente_id):
    try:
        paciente = Paciente.objects.get(id=paciente_id)
    except Paciente.DoesNotExist:
        return Response({"erro": "Paciente não encontrado"}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = PacienteSerializer(paciente)
        return JsonResponse(serializer.data, safe=False, json_dumps_params={'ensure_ascii': False})

    elif request.method == 'PUT':
        serializer = PacienteSerializer(paciente, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        paciente.delete()
        return Response({"mensagem": "Paciente deletado com sucesso"}, status=status.HTTP_204_NO_CONTENT)

@api_view(['GET'])
def exames_por_paciente(request, paciente_id):
    exames = Exame.objects.filter(paciente_id=paciente_id).order_by('-data_exame')
    serializer = ExameSerializer(exames, many=True)
    return JsonResponse(serializer.data, safe=False, json_dumps_params={'ensure_ascii': False})

@api_view(['GET'])
def exames_alelos_por_paciente_exame(request, paciente_id, exame_id):
    exames = Exame.objects.filter(id=exame_id, paciente_id=paciente_id)
    
    if not exames.exists():
        return Response({"erro": "Exame não encontrado para este paciente"}, status=status.HTTP_404_NOT_FOUND)

    exames_alelos = ExameAlelo.objects.filter(exame_id=exame_id).order_by('alelo__nome')
    serializer = ExameAleloSerializer(exames_alelos, many=True)
    return JsonResponse(serializer.data, safe=False, json_dumps_params={'ensure_ascii': False})


@api_view(['POST'])
def virtual_crossmatch(request):
    # Recebe a lista de alelos específicos com tipo e numero do front-end
    alelos_especificos = request.data.get('alelos', [])
    
    # Filtrar `Alelos` que correspondam ao tipo e numero dos alelos enviados
    alelo_filters = [
        (alelo['tipo'], int(alelo['numero']))
        for alelo in alelos_especificos if alelo['numero'] != "0"
    ]

    # Carregar dados para os DataFrames
    pacientes_df = pd.DataFrame(list(Paciente.objects.all().values('id', 'nome')))
    exames_df = pd.DataFrame(list(Exame.objects.all().values('id', 'paciente_id', 'data_exame')))
    
    # Filtra os alelos que correspondem ao `tipo` e `numero1` enviados
    exames_alelos_df = pd.DataFrame(list(
        ExameAlelo.objects.select_related('alelo')
        .filter(alelo__tipo__in=[f[0] for f in alelo_filters], alelo__numero1__in=[f[1] for f in alelo_filters])
        .values('exame_id', 'alelo__nome', 'valor', 'exame__paciente_id')
    ))

    # Encontra o último exame de cada paciente
    ultimos_exames = exames_df.loc[exames_df.groupby('paciente_id')['data_exame'].idxmax()]

    # Filtra os alelos específicos nos últimos exames de cada paciente
    exames_alelos_filtrados = exames_alelos_df[
        exames_alelos_df['exame_id'].isin(ultimos_exames['id'])
    ]

    # Para cada paciente, armazena os alelos correspondentes e seus valores
    pacientes_compatibilidade = {}
    for paciente_id, grupo in exames_alelos_filtrados.groupby('exame__paciente_id'):
        correspondencias = []
        for _, row in grupo.iterrows():
            correspondencias.append({
                'nome': row['alelo__nome'],
                'valor': row['valor'],
                'compatibilidade': row['valor'] < 1000  # True se o valor for < 1000, False caso contrário
            })
        pacientes_compatibilidade[paciente_id] = {
            'nome': pacientes_df[pacientes_df['id'] == paciente_id]['nome'].values[0],
            'alelos_correspondentes': correspondencias
        }

    # Retorna a compatibilidade para cada paciente no formato JSON
    return Response(pacientes_compatibilidade)


@api_view(['POST'])
def save_crossmatch_result(request):
    data = request.data
    print("Dados recebidos no backend:", data)  # Log dos dados recebidos

    try:
        # Verificação de campos obrigatórios no Crossmatch
        required_fields = ['donor_name', 'donor_sex', 'donor_birth_date', 'donor_blood_type', 'results']
        if not all(field in data for field in required_fields):
            return Response({"error": "Dados do doador incompletos ou inválidos."}, status=status.HTTP_400_BAD_REQUEST)

        # Cria o registro de crossmatch usando os dados do doador
        crossmatch = Crossmatch.objects.create(
            donor_id=data.get('donor_id'),  # Inclui o donor_id, se fornecido
            donor_name=data['donor_name'],
            donor_sex=data['donor_sex'],
            donor_birth_date=data['donor_birth_date'],
            donor_blood_type=data['donor_blood_type'],
            date_performed=datetime.now()
        )
        print("Crossmatch criado com ID:", crossmatch.id)

        # Processa cada resultado do paciente
        for patient_id, patient_data in data['results'].items():
            print("Processando paciente ID:", patient_id)  # Log do paciente
            if 'nome' not in patient_data or 'alelos_correspondentes' not in patient_data:
                return Response({"error": f"Dados do paciente {patient_id} incompletos."}, status=status.HTTP_400_BAD_REQUEST)

            total_compatible = sum(1 for alelo in patient_data['alelos_correspondentes'] if alelo['compatibilidade'])
            total_incompatible = sum(1 for alelo in patient_data['alelos_correspondentes'] if not alelo['compatibilidade'])
            
            # Cria o resultado do paciente
            patient_result = CrossmatchPatientResult.objects.create(
                crossmatch=crossmatch,
                patient_id=patient_id,
                patient_name=patient_data['nome'],
                total_compatible_alleles=total_compatible,
                total_incompatible_alleles=total_incompatible
            )
            print("Resultado do paciente criado com ID:", patient_result.id)

            # Processa cada alelo do paciente
            for allele in patient_data['alelos_correspondentes']:
                CrossmatchAlleleResult.objects.create(
                    patient_result=patient_result,
                    allele_name=allele['nome'],
                    allele_value=allele['valor'],
                    compatibility=allele['compatibilidade']
                )
                print("Alelo salvo:", allele['nome'], "Valor:", allele['valor'], "Compatibilidade:", allele['compatibilidade'])

        # Serializa o resultado completo para retornar na resposta
        crossmatch_serializer = CrossmatchSerializer(crossmatch)
        return Response(crossmatch_serializer.data, status=status.HTTP_201_CREATED)

    except Exception as e:
        print("Erro ao salvar crossmatch:", str(e))  # Log do erro
        return Response({"error": f"Erro ao salvar crossmatch: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

@api_view(['GET'])
def list_vxm(request):
    vxms = Crossmatch.objects.all().order_by('-date_performed')
    serialized_vxms = CrossmatchSerializer(vxms, many=True)
    return Response(serialized_vxms.data)

@api_view(['GET'])
def detail_vxm(request, vxm_id):
    try:
        vxm = Crossmatch.objects.get(id=vxm_id)
        serialized_vxm = CrossmatchSerializer(vxm)
        return Response(serialized_vxm.data)
    except Crossmatch.DoesNotExist:
        return Response({"error": "Crossmatch não encontrado"}, status=404)