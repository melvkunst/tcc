# Imagem base
FROM python:3.10

# Defina o diretório de trabalho
WORKDIR /app

# Copie o requirements.txt e instale as dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie o resto do código da aplicação para o diretório de trabalho
COPY . .

# Configura as variáveis de ambiente do Django
ENV DJANGO_SETTINGS_MODULE=tcc_back.settings
ENV PYTHONUNBUFFERED 1

# Exponha a porta 8000
EXPOSE 8000

# Comando para rodar o Django
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
