FROM python:3.12
COPY config.yml /config.yml
COPY gen-wiki.py /usr/bin/gen-wiki.py

ENV REPO_NAME="toto"

#Install dependencies
RUN apt-get update && \
    apt-get install -y jq && \
    python -m pip install --upgrade pip && \
    pip install pyaml

COPY --from=ghcr.io/skyscrapers/terragrunt:opentofu_v1.6.2 /usr/local/bin/sops /usr/local/bin/sops
COPY --from=ghcr.io/skyscrapers/terragrunt:opentofu_v1.6.2 /usr/local/bin/tofu /usr/local/bin/tofu
COPY --from=ghcr.io/skyscrapers/terragrunt:opentofu_v1.6.2 /usr/local/bin/terragrunt /usr/local/bin/terragrunt

#Code execution
ENTRYPOINT [ "python", "/usr/bin/gen-wiki.py", "/config.yml", "output/", $REPO_NAME ]