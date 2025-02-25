#!/bin/bash

# Atualiza o pip
python -m pip install --upgrade pip

# Instala dependências usando wheels pré-compilados
pip install --prefer-binary -r backend/requirements.txt