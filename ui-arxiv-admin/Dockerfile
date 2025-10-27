FROM node:22-alpine AS build
WORKDIR /app
COPY ./public ./public
COPY index.html .
COPY ./src ./src
COPY package*.json react-app.conf tsconfig.json vite.config.ts ./
RUN npm install
RUN npm run build:prod
FROM nginx:alpine AS production
COPY --from=build /app/dist/ /usr/share/nginx/html/admin-console/
COPY ./src /usr/share/nginx/html/src
COPY ./nginx/default.conf /etc/nginx/conf.d/default.conf
COPY ./nginx/nginx.conf /etc/nginx/nginx.conf
COPY nginx.sh /
RUN chmod +x /nginx.sh
EXPOSE 21511
CMD /nginx.sh
