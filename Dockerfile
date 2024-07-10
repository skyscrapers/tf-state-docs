FROM python:3.12
ADD . .

ENV REPO_NAME="toto"

#Install dependencies
RUN apt-get update
RUN apt-get install -y jq
RUN python -m pip install --upgrade pip
RUN pip install pyaml
RUN /install_terragrunt_tofu.sh 1.6.3

#Code execution
ENTRYPOINT [ "python", "gen-wiki.py", "config.yml", "output/", "$REPO_NAME" ]