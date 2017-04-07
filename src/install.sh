# requires python 3 and virtualenv are 
# installed and in execution path

virtualenv -p `which python3` venv
source venv/bin/activate
pip install -r requirements.txt
