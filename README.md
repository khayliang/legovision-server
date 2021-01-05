# legovision-server
Backend server for Lego block detection. Tasks include
- Receiving of video 
- Video processing for lego brick detection
- Saving of processed video
- Serving processed video
- Serving processed video detection information
# Setup
Run the following commands.

First, create environment in conda
```
conda env create -f environment.yml
```
Initialize environment
```
conda activate venv
```
Launch server
```
python main.py
```
