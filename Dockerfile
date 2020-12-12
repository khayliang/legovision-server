FROM continuumio/miniconda3
COPY . /app
WORKDIR /app
RUN apt-get update
RUN apt-get install ffmpeg libsm6 libxext6  -y
RUN conda config --add channels conda-forge
RUN conda config --set pip_interop_enabled True
RUN conda env create -f environment.yml
RUN echo "source activate venv" > ~/.bashrc
ENV PATH /opt/conda/envs/venv/bin:$PATH
ENTRYPOINT ["python"]
CMD ["main.py"]