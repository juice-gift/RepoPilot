FROM public.ecr.aws/docker/library/node@sha256:4b150b48b4116e2a22f2c39cc27025fbf4f153e2078fd3b14d159fdb5c7279da AS build
WORKDIR /app/apps/web
COPY apps/web/package.json apps/web/package-lock.json ./
RUN npm ci --ignore-scripts
COPY apps/web/index.html apps/web/tsconfig*.json apps/web/vite.config.ts ./
COPY apps/web/src ./src
ENV VITE_API_BASE_URL=""
RUN npm run build

FROM public.ecr.aws/docker/library/nginx@sha256:a8b39bd9cf0f83869a2162827a0caf6137ddf759d50a171451b335cecc87d236
COPY apps/web/nginx.conf /etc/nginx/nginx.conf
COPY --from=build /app/apps/web/dist /usr/share/nginx/html
USER 65534:65534
EXPOSE 8080
ENTRYPOINT ["nginx", "-g", "daemon off;"]
