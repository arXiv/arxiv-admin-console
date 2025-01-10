FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json react-app.conf tsconfig.json .
COPY ./public ./public
COPY ./src ./src
RUN npm install
RUN npm run build
FROM nginx:alpine AS production
COPY --from=build /app/build/ /usr/share/nginx/html/admin-console/
COPY ./src /usr/share/nginx/html/src
COPY ./nginx/default.conf /etc/nginx/conf.d/default.conf
COPY ./nginx/nginx.conf /etc/nginx/nginx.conf
COPY nginx.sh /
RUN chmod +x /nginx.sh
EXPOSE 4042
CMD /nginx.sh
