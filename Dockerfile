FROM alpine 
WORKDIR /daco2ego
RUN apk add --no-cache python3 
RUN apk add --no-cache bash 
RUN apk add --no-cache build-base 
ADD python/*.py ./requirements.txt ./ 
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt
EXPOSE 8081 
RUN apk add thttpd
RUN apk add openssl
RUN apk add curl
RUN apk add jq
ADD deploy/*.sh ./
ADD deploy/index.html deploy/*.cgi /uploads/
RUN chown -R nobody:nobody /uploads
RUN mkdir -p /daco2ego/files
RUN chown nobody:nobody /daco2ego/files
VOLUME config config
ENTRYPOINT ["./daco2ego.py"]
