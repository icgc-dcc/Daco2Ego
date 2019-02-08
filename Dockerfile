FROM alpine 
WORKDIR /daco2ego
RUN apk add --no-cache python3 
RUN apk add --no-cache bash 
RUN apk add --no-cache build-base 
ADD *.py requirements.txt ./ 
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt
EXPOSE 8081 
VOLUME config config
ENTRYPOINT ["bash"] 
