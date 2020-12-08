FROM continuumio/miniconda3
COPY . /app
WORKDIR /app
RUN conda config --add channels conda-forge
RUN conda env create -n venv -f requirements.txt
RUN echo "source activate venv" > ~/.bashrc
ENV PATH /opt/conda/envs/venv/bin:$PATH
ENTRYPOINT ["python"]
CMD ["main.py"]