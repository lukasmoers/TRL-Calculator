import os, pip
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

def install():
    try:
        pip.main(['install', '-r', 'requirements.txt'])
        if os.environ.get('SERVER') == "True":
            pip.main(['install', 'uWSGI==2.0.21'])
    except Exception as e:
        print(e)

if __name__ == '__main__':
    install()