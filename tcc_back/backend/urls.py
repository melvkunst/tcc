from django.urls import path
from . import views

urlpatterns = [ 
    path('api/pacientes/', views.lista_cria_pacientes, name='lista_cria_pacientes'),  # URL para listar e criar pacientes
    path('api/pacientes/<int:paciente_id>/', views.detalhe_paciente, name='detalhe_paciente'),  # URL para acessar, visualizar e atualizar um paciente específico
    path('api/pacientes/<int:paciente_id>/exames/', views.exames_por_paciente, name='exames_por_paciente'),  # URL para acessar exames de um paciente específico
    path('api/pacientes/<int:paciente_id>/exames/<int:exame_id>/alelos/', views.exames_alelos_por_paciente_exame, name='exames_alelos_por_paciente_exame'),  # URL para acessar alelos de um exame específico
    path('newvxm/virtual_crossmatch/', views.virtual_crossmatch, name='virtual_crossmatch'),
    path('save_crossmatch_result/', views.save_crossmatch_result, name='save_crossmatch_result'),
    path('vxm-history/', views.list_vxm, name='vxm_history'),  # Listar todos os VXMs
    path('vxm-details/<int:vxm_id>/', views.detail_vxm, name='vxm_details'),  # Detalhes de um VXM
]
