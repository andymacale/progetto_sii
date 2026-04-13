# Base ufficiale NVIDIA
FROM nvcr.io/nvidia/pytorch:25.02-py3

# Installiamo LaTeX (lo facciamo QUI una volta per tutte)
RUN apt-get update && apt-get install -y \
    texlive-latex-base \
    texlive-fonts-recommended \
    texlive-latex-extra \
    && rm -rf /var/lib/apt/lists/*

# Installiamo le dipendenze Python
COPY web_app/requirements.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt python-dotenv