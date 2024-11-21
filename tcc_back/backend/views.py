from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status, generics
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.models import User
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.conf import settings  # Import settings to access SECRET_KEY
import pandas as pd
from django.http import JsonResponse
from .models import Paciente, Exame, ExameAlelo, Alelo, Crossmatch, CrossmatchPatientResult, CrossmatchAlleleResult
from .serializers import PacienteSerializer, ExameSerializer, ExameAleloSerializer, CrossmatchSerializer, CrossmatchPatientResultSerializer, CrossmatchAlleleResultSerializer, UserSerializer
from datetime import datetime
from django.shortcuts import get_object_or_404
import logging
import json
from rest_framework.decorators import permission_classes

# Configuração do logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class CreateUserView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

@api_view(['GET', 'POST'])
@permission_classes([])
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
@permission_classes([])
def detalhe_paciente(request, paciente_id):
    try:
        # Buscar o paciente pelo ID
        paciente = Paciente.objects.get(id=paciente_id)
    except Paciente.DoesNotExist:
        return Response({"erro": "Paciente não encontrado"}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        # Retornar os detalhes do paciente
        serializer = PacienteSerializer(paciente)
        return JsonResponse(serializer.data, safe=False, json_dumps_params={'ensure_ascii': False})

    elif request.method == 'PUT':
        # Atualizar os dados do paciente
        serializer = PacienteSerializer(paciente, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        # Excluir os crossmatches relacionados ao paciente
        crossmatch_patient_results = CrossmatchPatientResult.objects.filter(patient_id=paciente_id)
        for result in crossmatch_patient_results:
            # Deletar os alelos associados ao resultado
            CrossmatchAlleleResult.objects.filter(patient_result=result).delete()
            # Deletar o resultado do paciente no crossmatch
            result.delete()

        # Excluir o paciente e seus exames (cascata devido a `on_delete=models.CASCADE`)
        paciente.delete()

        return Response({"mensagem": "Paciente e dados relacionados deletados com sucesso"}, status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
@permission_classes([])
def exames_por_paciente(request, paciente_id):
    exames = Exame.objects.filter(paciente_id=paciente_id).order_by('-data_exame')
    serializer = ExameSerializer(exames, many=True)
    return JsonResponse(serializer.data, safe=False, json_dumps_params={'ensure_ascii': False})

@api_view(['GET'])
@permission_classes([])
def exames_alelos_por_paciente_exame(request, paciente_id, exame_id):
    exames = Exame.objects.filter(id=exame_id, paciente_id=paciente_id)
    
    if not exames.exists():
        return Response({"erro": "Exame não encontrado para este paciente"}, status=status.HTTP_404_NOT_FOUND)

    exames_alelos = ExameAlelo.objects.filter(exame_id=exame_id).order_by('alelo__nome')
    serializer = ExameAleloSerializer(exames_alelos, many=True)
    return JsonResponse(serializer.data, safe=False, json_dumps_params={'ensure_ascii': False})


@api_view(['GET'])
@permission_classes([])  # Atualize a permissão conforme necessário (ex.: [IsAuthenticated])
def lista_exames(request):
    """
    Retorna a lista de todos os exames.
    """
    try:
        exames = Exame.objects.all().order_by('-data_exame')  # Ordena por data decrescente
        serializer = ExameSerializer(exames, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": f"Erro ao buscar exames: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([])  # Atualize a permissão conforme necessário
def detalhe_exame(request, exame_id):
    """
    Retorna os detalhes de um exame específico.
    """
    try:
        exame = get_object_or_404(Exame, id=exame_id)
        serializer = ExameSerializer(exame)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": f"Erro ao buscar detalhes do exame: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([])
def virtual_crossmatch(request):
    
    # Recebe a lista de alelos específicos com tipo e número do front-end
    alelos_especificos = request.data.get('alelos', [])
    logger.info(f"Payload recebido: {json.dumps(request.data)}")
    donor_blood_type = request.data.get('donor_blood_type')  # Recebe o tipo sanguíneo do doador
    if donor_blood_type is None:
        logger.info("Tipo sanguíneo ausente ou inválido")

    # Log do tipo sanguíneo do doador
    logger.info(f"Tipo sanguíneo do doador: {donor_blood_type}")

    # Filtrar `Alelos` que correspondam ao tipo e número dos alelos enviados
    alelo_filters = [
        (alelo['tipo'], int(alelo['numero']))
        for alelo in alelos_especificos if alelo['numero'] != "0"
    ]

    # Carregar dados para os DataFrames, incluindo filtro por tipo sanguíneo
    pacientes = Paciente.objects.filter(tipo_sanguineo=donor_blood_type).values('id', 'nome', 'tipo_sanguineo')
    pacientes_df = pd.DataFrame(list(pacientes))

    # Log dos tipos sanguíneos dos pacientes encontrados
    logger.info(f"Pacientes com tipo sanguíneo compatível: {list(pacientes)}")

    # Caso não existam pacientes com o tipo sanguíneo correspondente, retornar vazio
    if pacientes_df.empty:
        logger.warning("Nenhum paciente encontrado com o tipo sanguíneo compatível.")
        return Response({"message": "Nenhum paciente encontrado com o tipo sanguíneo compatível."}, status=404)

    exames_df = pd.DataFrame(list(Exame.objects.all().values('id', 'paciente_id', 'data_exame')))

    # Filtra os alelos que correspondem ao `tipo` e `numero1` enviados
    exames_alelos_df = pd.DataFrame(list(
        ExameAlelo.objects.select_related('alelo')
        .filter(alelo__tipo__in=[f[0] for f in alelo_filters], alelo__numero1__in=[f[1] for f in alelo_filters])
        .values('exame_id', 'alelo__nome', 'valor', 'exame__paciente_id')
    ))

    # Encontra o último exame de cada paciente
    ultimos_exames = exames_df.loc[exames_df.groupby('paciente_id')['data_exame'].idxmax()]

    # Filtra os alelos específicos nos últimos exames de cada paciente com tipo sanguíneo igual ao do doador
    exames_alelos_filtrados = exames_alelos_df[
        exames_alelos_df['exame_id'].isin(ultimos_exames['id']) &
        exames_alelos_df['exame__paciente_id'].isin(pacientes_df['id'])
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

    # Log dos resultados finais
    logger.info(f"Compatibilidade dos pacientes: {pacientes_compatibilidade}")

    # Retorna a compatibilidade para cada paciente no formato JSON
    return Response(pacientes_compatibilidade)


@api_view(['POST'])
@permission_classes([])
def save_crossmatch_result(request):
    data = request.data
    logger.info("Dados recebidos no backend: %s", data)  # Log dos dados recebidos

    try:
        # Verificação de campos obrigatórios no Crossmatch
        required_fields = ['donor_name', 'donor_sex', 'donor_birth_date', 'donor_blood_type', 'results']
        if not all(field in data for field in required_fields):
            logger.error("Dados do doador incompletos ou inválidos.")
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
        logger.info("Crossmatch criado com ID: %s", crossmatch.id)

        # Processa cada resultado do paciente
        for patient_id, patient_data in data['results'].items():
            logger.info("Processando paciente ID: %s, Nome: %s", patient_id, patient_data.get('nome'))
            if 'nome' not in patient_data or 'alelos_correspondentes' not in patient_data:
                logger.error("Dados do paciente %s incompletos.", patient_id)
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
            logger.info("Resultado do paciente criado com ID: %s, Total Compatível: %d, Total Incompatível: %d",
                        patient_result.id, total_compatible, total_incompatible)

            # Processa cada alelo do paciente
            for allele in patient_data['alelos_correspondentes']:
                logger.info("Salvando alelo: Nome: %s, Valor: %s, Compatibilidade: %s",
                            allele['nome'], allele['valor'], allele['compatibilidade'])
                try:
                    CrossmatchAlleleResult.objects.create(
                        patient_result=patient_result,
                        allele_name=allele['nome'],
                        allele_value=allele['valor'],
                        compatibility=allele['compatibilidade']
                    )
                    logger.info("Alelo salvo com sucesso: %s", allele['nome'])
                except Exception as allele_error:
                    logger.error("Erro ao salvar alelo %s: %s", allele['nome'], allele_error)
                    raise allele_error

        # Serializa o resultado completo para retornar na resposta
        crossmatch_serializer = CrossmatchSerializer(crossmatch)
        logger.info("Crossmatch processado com sucesso.")
        return Response(crossmatch_serializer.data, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error("Erro ao salvar crossmatch: %s", str(e))  # Log do erro
        return Response({"error": f"Erro ao salvar crossmatch: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(['GET'])
@permission_classes([])
def list_vxm(request):
    vxms = Crossmatch.objects.all().order_by('-date_performed')
    serialized_vxms = CrossmatchSerializer(vxms, many=True)
    return Response(serialized_vxms.data)

@api_view(['GET'])
@permission_classes([])
def detail_vxm(request, vxm_id):
    try:
        vxm = Crossmatch.objects.get(id=vxm_id)
        serialized_vxm = CrossmatchSerializer(vxm)
        return Response(serialized_vxm.data)
    except Crossmatch.DoesNotExist:
        return Response({"error": "Crossmatch não encontrado"}, status=404)
    


# Configurar logging
logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([])
def upload_excel(request, patient_id):
    file = request.FILES.get('file')
    if not file:
        return JsonResponse({"error": "Nenhum arquivo foi enviado."}, status=400)

    # Verificar extensão do arquivo
    file_extension = file.name.split('.')[-1].lower()
    try:
        if file_extension == 'xlsx':
            df = pd.read_excel(file, engine='openpyxl')
        elif file_extension == 'xls':
            df = pd.read_excel(file, engine='xlrd')
        else:
            return JsonResponse({"error": "Formato de arquivo não suportado. Use arquivos .xls ou .xlsx."}, status=400)
    except Exception as e:
        return JsonResponse({"error": f"Erro ao processar o arquivo Excel: {str(e)}"}, status=400)

    # Preencher valores NaN com strings vazias
    df = df.fillna('')

    # Verificar a presença de "TEST DATE" para obter a data do exame
    test_date_cell = df[df.apply(lambda row: row.astype(str).str.contains('TEST DATE', case=False).any(), axis=1)]
    if not test_date_cell.empty:
        row_idx = test_date_cell.index[0]
        col_idx = df.columns.get_loc(
            test_date_cell.columns[test_date_cell.iloc[0].astype(str).str.contains("TEST DATE", case=False)][0]
        )
        exam_date_str = df.iat[row_idx, col_idx + 4]

        # Converter a data
        try:
            if isinstance(exam_date_str, str):
                exam_date = datetime.strptime(exam_date_str, "%d/%m/%Y").date()
            elif isinstance(exam_date_str, datetime):
                exam_date = exam_date_str.date()
            else:
                raise ValueError
        except ValueError:
            return JsonResponse({"error": "Data do exame ausente ou em formato incorreto."}, status=400)
    else:
        return JsonResponse({"error": "Campo 'TEST DATE' não encontrado."}, status=400)

    # Verificar se o paciente existe
    paciente = get_object_or_404(Paciente, id=patient_id)

    try:
        # Definir as colunas de alelo e valor "Raw"
        alelo_col = df.iloc[9:, 35]  # Coluna AJ para 'Allele Specificity'
        raw_col = df.iloc[9:, 3]     # Coluna D para 'Raw'

        # Criar ou obter o exame
        exame, created = Exame.objects.get_or_create(paciente=paciente, data_exame=exam_date)

        # Processar cada linha das colunas de alelos e valores
        for alelo_name, raw_value in zip(alelo_col, raw_col):
            # Ignorar células que só têm "-" ou espaços e vírgulas
            if not alelo_name or alelo_name.strip() in ["-", "", None]:
                continue
            
            # Separar múltiplos valores no campo de alelo
            alelo_name = alelo_name.split(",")
            
            # Processar cada alelo válido na lista
            for main_alelo in alelo_name:
                main_alelo = main_alelo.strip()
                if main_alelo in ["-", "", None]:
                    continue  # Ignorar células vazias ou com marcador "-"

                # Separar tipo, numero1 e numero2
                if '*' in main_alelo:
                    tipo = main_alelo[:2]  # Extrair apenas os dois primeiros caracteres para o campo `tipo`
                    numeros = main_alelo.split('*')[1]
                    try:
                        numero1, numero2 = map(int, numeros.split(':'))
                    except ValueError:
                        logger.warning(f"Alelo malformado ignorado: {main_alelo}")
                        continue  # Pular alelos com formato incorreto
                else:
                    logger.warning(f"Alelo malformado ignorado: {main_alelo}")
                    continue  # Pular alelos malformados ou sem '*'

                # Verificar ou criar alelo
                alelo, created = Alelo.objects.get_or_create(
                    nome=main_alelo,
                    defaults={'tipo': tipo, 'numero1': numero1, 'numero2': numero2}
                )

                # Converter o valor para float, substituindo vírgula por ponto
                try:
                    raw_value = float(str(raw_value).replace(',', '.'))
                except ValueError:
                    logger.warning(f"Valor incorreto para o alelo {main_alelo}: {raw_value}")
                    continue  # Ignorar valores inválidos

                logger.info(f"Processando alelo: {main_alelo} com valor: {raw_value}")

                # Verificar se já existe uma entrada para esse alelo no exame
                if ExameAlelo.objects.filter(exame=exame, alelo=alelo).exists():
                    # Se já existe, adicionar um sufixo para evitar duplicação
                    sufixo = 1
                    novo_nome = f"{main_alelo}.{sufixo}"
                    while Alelo.objects.filter(nome=novo_nome).exists():
                        sufixo += 1
                        novo_nome = f"{main_alelo}.{sufixo}"
                    alelo = Alelo.objects.create(
                        nome=novo_nome,
                        tipo=tipo,
                        numero1=numero1,
                        numero2=numero2
                    )

                # Associar o alelo ao exame
                ExameAlelo.objects.create(exame=exame, alelo=alelo, valor=raw_value)

        return JsonResponse({"message": "Exame e alelos processados com sucesso."}, status=201)
    except Exception as e:
        logger.error(f"Erro ao processar o exame: {str(e)}")
        return JsonResponse({"error": f"Erro ao processar o exame: {str(e)}"}, status=500)
