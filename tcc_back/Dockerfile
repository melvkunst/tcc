# Use uma imagem base com Python
FROM python:3.10

# Defina o diretório de trabalho
WORKDIR /app/tcc_back

# Copie o arquivo de dependências para o container
COPY requirements.txt /app/

# Instale as dependências
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copie o resto do código da aplicação para o diretório de trabalho
COPY . /app/

# Configura variáveis de ambiente Django
ENV DJANGO_SETTINGS_MODULE=tcc_back.settings
ENV PYTHONUNBUFFERED 1

# Exponha a porta 8000 para o Django
EXPOSE 8000

# Comando para rodar o Django
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
