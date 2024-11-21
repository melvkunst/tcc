from django.urls import path
from . import views

urlpatterns = [

    # Pacientes
    path('pacientes/', views.lista_cria_pacientes, name='lista_cria_pacientes'),  # Listar e criar pacientes
    path('pacientes/<int:paciente_id>/', views.detalhe_paciente, name='detalhe_paciente'),  # Visualizar e atualizar paciente específico
    path('pacientes/<int:paciente_id>/exames/', views.exames_por_paciente, name='exames_por_paciente'),  # Exames de um paciente
    path('pacientes/<int:paciente_id>/exames/<int:exame_id>/alelos/', views.exames_alelos_por_paciente_exame, name='exames_alelos_por_paciente_exame'),  # Alelos de um exame específico
    path('pacientes/<int:patient_id>/exames/upload/', views.upload_excel, name='upload_excel'),  # Upload de exames via Excel

    # Virtual Crossmatch
    path('newvxm/virtual_crossmatch/', views.virtual_crossmatch, name='virtual_crossmatch'),  # Realizar novo Virtual Crossmatch
    path('save_crossmatch_result/', views.save_crossmatch_result, name='save_crossmatch_result'),  # Salvar resultados do Virtual Crossmatch

    # VXM History and Details
    path('vxm-history/', views.list_vxm, name='vxm_history'),  # Listar todos os VXMs
    path('vxm-details/<int:vxm_id>/', views.detail_vxm, name='vxm_details'),  # Detalhes de um VXM específico

    path('exames/', views.lista_exames, name='lista_exames'),
    path('exames/<int:exame_id>/', views.detalhe_exame, name='detalhe_exame'),
]
