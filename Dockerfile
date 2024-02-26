FROM node:hydrogen

WORKDIR /app

COPY ./package.json /app/package.json
RUN npm install

COPY ./server.js /app/server.js
COPY ./frames/ /app/frames/

CMD [ "npm", "start" ]